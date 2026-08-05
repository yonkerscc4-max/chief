"""Aggregations over raw Toast API payloads.

These are pure functions over already-fetched data so they can be unit tested
without network access, and so the same order pull can feed several reports.

A note on money: Toast returns amounts as JSON numbers in dollars. Everything
here converts through ``str`` into ``Decimal`` before summing, so repeated
addition of values like 0.1 does not drift.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

ZERO = Decimal("0")

# Toast pays overtime at time-and-a-half. Restaurants with a different agreement
# should override this before trusting the estimated-pay columns.
OVERTIME_MULTIPLIER = Decimal("1.5")


def money(value) -> Decimal:
    """Coerce a Toast numeric field to Decimal dollars, treating null as zero."""
    if value is None:
        return ZERO
    return Decimal(str(value))


def _is_live(record: dict) -> bool:
    """True unless the record was voided or deleted.

    Voided checks and orders stay in the API response, so every aggregation has
    to filter them out or sales come back overstated.
    """
    return not record.get("voided") and not record.get("deleted")


def sales_summary(orders) -> dict:
    """Roll a stream of orders into one sales report.

    Net sales are the pre-tax check totals after discounts, matching the "Net
    sales" line in Toast's own sales summary.
    """
    summary = {
        "orders": 0,
        "checks": 0,
        "guests": 0,
        "net_sales": ZERO,
        "tax": ZERO,
        "tips": ZERO,
        "discounts": ZERO,
        "service_charges": ZERO,
        "gratuity_service_charges": ZERO,
        "total_collected": ZERO,
        "refunds": ZERO,
        "voided_checks": 0,
        "by_payment_type": defaultdict(lambda: {"count": 0, "amount": ZERO, "tips": ZERO}),
        "by_dining_option": defaultdict(lambda: {"count": 0, "net_sales": ZERO}),
        "by_revenue_center": defaultdict(lambda: {"count": 0, "net_sales": ZERO}),
    }

    for order in orders:
        if not _is_live(order):
            continue

        order_checks = order.get("checks") or []
        live_checks = [check for check in order_checks if _is_live(check)]
        summary["voided_checks"] += len(order_checks) - len(live_checks)
        if not live_checks:
            continue

        summary["orders"] += 1
        summary["guests"] += order.get("numberOfGuests") or 0

        dining_option = _label(order.get("diningOption"), "Unspecified")
        revenue_center = _label(order.get("revenueCenter"), "Unspecified")

        for check in live_checks:
            summary["checks"] += 1
            net = money(check.get("amount"))
            summary["net_sales"] += net
            summary["tax"] += money(check.get("taxAmount"))

            for discount in check.get("appliedDiscounts") or []:
                summary["discounts"] += money(discount.get("discountAmount"))

            for charge in check.get("appliedServiceCharges") or []:
                amount = money(charge.get("chargeAmount"))
                summary["service_charges"] += amount
                if charge.get("gratuity"):
                    summary["gratuity_service_charges"] += amount

            for payment in check.get("payments") or []:
                if payment.get("paymentStatus") == "VOIDED" or payment.get("voidInfo"):
                    continue
                amount = money(payment.get("amount"))
                tip = money(payment.get("tipAmount"))
                summary["tips"] += tip
                summary["total_collected"] += amount + tip

                refund = payment.get("refund") or {}
                summary["refunds"] += money(refund.get("refundAmount")) + money(refund.get("tipRefundAmount"))

                bucket = summary["by_payment_type"][payment.get("type") or "UNKNOWN"]
                bucket["count"] += 1
                bucket["amount"] += amount
                bucket["tips"] += tip

            summary["by_dining_option"][dining_option]["count"] += 1
            summary["by_dining_option"][dining_option]["net_sales"] += net
            summary["by_revenue_center"][revenue_center]["count"] += 1
            summary["by_revenue_center"][revenue_center]["net_sales"] += net

    summary["average_check"] = (
        (summary["net_sales"] / summary["checks"]) if summary["checks"] else ZERO
    )
    summary["by_payment_type"] = dict(summary["by_payment_type"])
    summary["by_dining_option"] = dict(summary["by_dining_option"])
    summary["by_revenue_center"] = dict(summary["by_revenue_center"])
    return summary


def transactions(orders) -> list[dict]:
    """Flatten orders into one row per payment, newest last.

    This is the grain most people mean by "transactions" -- an individual tender
    against a check, with enough context to reconcile against a bank deposit.
    """
    rows: list[dict] = []

    for order in orders:
        if not _is_live(order):
            continue
        for check in order.get("checks") or []:
            if not _is_live(check):
                continue
            for payment in check.get("payments") or []:
                refund = payment.get("refund") or {}
                rows.append(
                    {
                        "paid_date": payment.get("paidDate"),
                        "business_date": payment.get("paidBusinessDate"),
                        "order_guid": order.get("guid"),
                        "check_guid": check.get("guid"),
                        "payment_guid": payment.get("guid"),
                        "check_number": check.get("displayNumber"),
                        "tab_name": check.get("tabName"),
                        "type": payment.get("type"),
                        "card_type": payment.get("cardType"),
                        "last4": payment.get("last4Digits"),
                        "entry_mode": payment.get("cardEntryMode"),
                        "amount": money(payment.get("amount")),
                        "tip": money(payment.get("tipAmount")),
                        "total": money(payment.get("amount")) + money(payment.get("tipAmount")),
                        "status": payment.get("paymentStatus"),
                        "refund_status": payment.get("refundStatus"),
                        "refund_amount": money(refund.get("refundAmount")),
                        "server_guid": (payment.get("server") or {}).get("guid"),
                        "voided": bool(payment.get("voidInfo")),
                    }
                )

    rows.sort(key=lambda row: row["paid_date"] or "")
    return rows


def labor_summary(time_entries, employee_names: dict[str, str] | None = None) -> dict:
    """Roll time entries into per-employee hours, tips, and estimated pay.

    Estimated pay is ``hours x wage`` straight from the time entries. It is a
    labor-cost estimate for management reporting -- it is not a payroll
    calculation and does not account for taxes, deductions, benefits, salaried
    staff, or wage changes mid-period.
    """
    employee_names = employee_names or {}
    per_employee: dict[str, dict] = {}

    for entry in time_entries:
        if entry.get("deleted"):
            continue

        guid = (entry.get("employeeReference") or {}).get("guid") or "unknown"
        record = per_employee.setdefault(
            guid,
            {
                "employee_guid": guid,
                "name": employee_names.get(guid, guid),
                "shifts": 0,
                "regular_hours": ZERO,
                "overtime_hours": ZERO,
                "declared_cash_tips": ZERO,
                "non_cash_tips": ZERO,
                "tips_withheld": ZERO,
                "estimated_pay": ZERO,
                "open_shifts": 0,
                "missed_breaks": 0,
            },
        )

        regular = money(entry.get("regularHours"))
        overtime = money(entry.get("overtimeHours"))
        wage = money(entry.get("hourlyWage"))

        record["shifts"] += 1
        record["regular_hours"] += regular
        record["overtime_hours"] += overtime
        record["declared_cash_tips"] += money(entry.get("declaredCashTips"))
        record["non_cash_tips"] += money(entry.get("nonCashTips"))
        record["tips_withheld"] += money(entry.get("tipsWithheld"))
        record["estimated_pay"] += regular * wage + overtime * wage * OVERTIME_MULTIPLIER

        if not entry.get("outDate"):
            record["open_shifts"] += 1
        record["missed_breaks"] += sum(1 for brk in entry.get("breaks") or [] if brk.get("missed"))

    employees = sorted(per_employee.values(), key=lambda row: row["name"].lower())
    totals = {
        "employees": len(employees),
        "shifts": sum(row["shifts"] for row in employees),
        "regular_hours": sum((row["regular_hours"] for row in employees), ZERO),
        "overtime_hours": sum((row["overtime_hours"] for row in employees), ZERO),
        "declared_cash_tips": sum((row["declared_cash_tips"] for row in employees), ZERO),
        "non_cash_tips": sum((row["non_cash_tips"] for row in employees), ZERO),
        "estimated_pay": sum((row["estimated_pay"] for row in employees), ZERO),
        "open_shifts": sum(row["open_shifts"] for row in employees),
        "missed_breaks": sum(row["missed_breaks"] for row in employees),
    }
    return {"employees": employees, "totals": totals}


def _label(reference: dict | None, fallback: str) -> str:
    """Best available human label for a Toast entity reference."""
    if not reference:
        return fallback
    return reference.get("name") or reference.get("guid") or fallback
