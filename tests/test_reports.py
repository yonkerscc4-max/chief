"""Tests for the report aggregations.

Fixtures mirror the payload shapes in Toast's published OpenAPI response
samples for /orders/v2/ordersBulk and /labor/v1/timeEntries.
"""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toast.reports import labor_summary, sales_summary, transactions  # noqa: E402


def check(amount, tax, payments=None, **overrides):
    base = {
        "guid": "check-1",
        "amount": amount,
        "taxAmount": tax,
        "totalAmount": amount + tax,
        "payments": payments or [],
        "appliedDiscounts": [],
        "appliedServiceCharges": [],
        "voided": False,
        "deleted": False,
    }
    base.update(overrides)
    return base


def order(checks, **overrides):
    base = {
        "guid": "order-1",
        "checks": checks,
        "numberOfGuests": 2,
        "voided": False,
        "deleted": False,
        "diningOption": {"guid": "d1", "name": "Dine In"},
        "revenueCenter": {"guid": "r1", "name": "Bar"},
    }
    base.update(overrides)
    return base


def payment(amount, tip=0, ptype="CREDIT", **overrides):
    base = {
        "guid": "pay-1",
        "type": ptype,
        "amount": amount,
        "tipAmount": tip,
        "paymentStatus": "CAPTURED",
        "paidDate": "2026-08-04T18:00:00Z",
    }
    base.update(overrides)
    return base


class SalesSummaryTests(unittest.TestCase):
    def test_totals_across_checks(self):
        orders = [
            order([check(100.00, 8.00, [payment(100.00, 20.00)])]),
            order([check(50.00, 4.00, [payment(54.00, 0, "CASH")])], guid="order-2"),
        ]
        result = sales_summary(orders)

        self.assertEqual(result["orders"], 2)
        self.assertEqual(result["checks"], 2)
        self.assertEqual(result["net_sales"], Decimal("150.00"))
        self.assertEqual(result["tax"], Decimal("12.00"))
        self.assertEqual(result["tips"], Decimal("20.00"))
        self.assertEqual(result["total_collected"], Decimal("174.00"))
        self.assertEqual(result["average_check"], Decimal("75.00"))

    def test_voided_and_deleted_are_excluded(self):
        orders = [
            order([check(100.00, 8.00, [payment(100.00)])]),
            order([check(999.00, 99.00, [payment(999.00)])], guid="order-2", voided=True),
            order([check(500.00, 50.00, [payment(500.00)])], guid="order-3", deleted=True),
        ]
        result = sales_summary(orders)

        self.assertEqual(result["orders"], 1)
        self.assertEqual(result["net_sales"], Decimal("100.00"))

    def test_voided_check_within_live_order_is_counted_but_not_summed(self):
        orders = [
            order(
                [
                    check(100.00, 8.00, [payment(100.00)]),
                    check(60.00, 5.00, [payment(60.00)], guid="check-2", voided=True),
                ]
            )
        ]
        result = sales_summary(orders)

        self.assertEqual(result["checks"], 1)
        self.assertEqual(result["voided_checks"], 1)
        self.assertEqual(result["net_sales"], Decimal("100.00"))

    def test_order_with_only_voided_checks_is_not_an_order(self):
        orders = [order([check(60.00, 5.00, [payment(60.00)], voided=True)])]
        result = sales_summary(orders)

        self.assertEqual(result["orders"], 0)
        self.assertEqual(result["voided_checks"], 1)
        self.assertEqual(result["net_sales"], Decimal("0"))

    def test_voided_payment_is_not_collected(self):
        orders = [
            order([check(100.00, 8.00, [payment(100.00, 20.00, voidInfo={"voidBusinessDate": 20260804})])])
        ]
        result = sales_summary(orders)

        self.assertEqual(result["total_collected"], Decimal("0"))
        self.assertEqual(result["tips"], Decimal("0"))
        # The sale itself still happened; only the tender was voided.
        self.assertEqual(result["net_sales"], Decimal("100.00"))

    def test_discounts_service_charges_and_gratuity(self):
        orders = [
            order(
                [
                    check(
                        90.00,
                        7.20,
                        [payment(97.20)],
                        appliedDiscounts=[{"discountAmount": 10.00}],
                        appliedServiceCharges=[
                            {"chargeAmount": 18.00, "gratuity": True},
                            {"chargeAmount": 3.00, "gratuity": False},
                        ],
                    )
                ]
            )
        ]
        result = sales_summary(orders)

        self.assertEqual(result["discounts"], Decimal("10.00"))
        self.assertEqual(result["service_charges"], Decimal("21.00"))
        self.assertEqual(result["gratuity_service_charges"], Decimal("18.00"))

    def test_breakdown_by_payment_type(self):
        orders = [
            order([check(100.00, 0, [payment(100.00, 15.00, "CREDIT")])]),
            order([check(40.00, 0, [payment(40.00, 0, "CASH")])], guid="order-2"),
            order([check(60.00, 0, [payment(60.00, 5.00, "CREDIT")])], guid="order-3"),
        ]
        result = sales_summary(orders)

        self.assertEqual(result["by_payment_type"]["CREDIT"]["count"], 2)
        self.assertEqual(result["by_payment_type"]["CREDIT"]["amount"], Decimal("160.00"))
        self.assertEqual(result["by_payment_type"]["CREDIT"]["tips"], Decimal("20.00"))
        self.assertEqual(result["by_payment_type"]["CASH"]["amount"], Decimal("40.00"))

    def test_decimal_addition_does_not_drift(self):
        orders = [order([check(0.10, 0, [payment(0.10)])], guid=f"o{i}") for i in range(10)]
        result = sales_summary(orders)

        self.assertEqual(result["net_sales"], Decimal("1.00"))

    def test_empty_input(self):
        result = sales_summary([])

        self.assertEqual(result["orders"], 0)
        self.assertEqual(result["net_sales"], Decimal("0"))
        self.assertEqual(result["average_check"], Decimal("0"))


class TransactionsTests(unittest.TestCase):
    def test_one_row_per_payment_sorted_by_paid_date(self):
        orders = [
            order(
                [
                    check(
                        100.00,
                        8.00,
                        [
                            payment(60.00, 10.00, guid="p2", paidDate="2026-08-04T19:00:00Z"),
                            payment(48.00, 5.00, guid="p1", paidDate="2026-08-04T18:00:00Z"),
                        ],
                    )
                ]
            )
        ]
        rows = transactions(orders)

        self.assertEqual([row["payment_guid"] for row in rows], ["p1", "p2"])
        self.assertEqual(rows[0]["total"], Decimal("53.00"))
        self.assertEqual(rows[1]["total"], Decimal("70.00"))

    def test_voided_orders_produce_no_rows(self):
        orders = [order([check(100.00, 8.00, [payment(100.00)])], voided=True)]

        self.assertEqual(transactions(orders), [])


class LaborSummaryTests(unittest.TestCase):
    @staticmethod
    def entry(guid, regular, overtime=0, wage=20.00, **overrides):
        base = {
            "guid": f"te-{guid}-{regular}",
            "employeeReference": {"guid": guid},
            "regularHours": regular,
            "overtimeHours": overtime,
            "hourlyWage": wage,
            "declaredCashTips": 0,
            "nonCashTips": 0,
            "tipsWithheld": 0,
            "inDate": "2026-08-04T16:00:00Z",
            "outDate": "2026-08-04T24:00:00Z",
            "breaks": [],
            "deleted": False,
        }
        base.update(overrides)
        return base

    def test_hours_and_pay_roll_up_per_employee(self):
        entries = [
            self.entry("e1", 8.0),
            self.entry("e1", 6.0, overtime=2.0),
            self.entry("e2", 5.0, wage=18.00),
        ]
        report = labor_summary(entries, {"e1": "Alex Rivera", "e2": "Sam Chen"})

        alex = next(row for row in report["employees"] if row["name"] == "Alex Rivera")
        self.assertEqual(alex["shifts"], 2)
        self.assertEqual(alex["regular_hours"], Decimal("14.0"))
        self.assertEqual(alex["overtime_hours"], Decimal("2.0"))
        # 14 regular hours at $20 plus 2 overtime hours at $30.
        self.assertEqual(alex["estimated_pay"], Decimal("340.00"))

        self.assertEqual(report["totals"]["employees"], 2)
        self.assertEqual(report["totals"]["estimated_pay"], Decimal("430.00"))

    def test_open_shift_and_missed_break_are_flagged(self):
        entries = [
            self.entry("e1", 4.0, outDate=None),
            self.entry("e1", 8.0, breaks=[{"missed": True}, {"missed": False}]),
        ]
        report = labor_summary(entries)

        self.assertEqual(report["totals"]["open_shifts"], 1)
        self.assertEqual(report["totals"]["missed_breaks"], 1)

    def test_deleted_entries_are_ignored(self):
        entries = [self.entry("e1", 8.0), self.entry("e1", 99.0, deleted=True)]
        report = labor_summary(entries)

        self.assertEqual(report["totals"]["regular_hours"], Decimal("8.0"))

    def test_falls_back_to_guid_when_name_unknown(self):
        report = labor_summary([self.entry("e9", 3.0)])

        self.assertEqual(report["employees"][0]["name"], "e9")

    def test_null_money_fields_are_treated_as_zero(self):
        entries = [self.entry("e1", 8.0, declaredCashTips=None, nonCashTips=None, hourlyWage=None)]
        report = labor_summary(entries)

        self.assertEqual(report["totals"]["declared_cash_tips"], Decimal("0"))
        self.assertEqual(report["totals"]["estimated_pay"], Decimal("0"))


if __name__ == "__main__":
    unittest.main()
