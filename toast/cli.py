"""Command line entry point for pulling Toast reports.

    python -m toast check
    python -m toast sales --business-date 2026-08-04
    python -m toast sales --days 7
    python -m toast transactions --business-date 2026-08-04 --format csv
    python -m toast labor --start 2026-07-21 --end 2026-08-04
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .client import ToastClient, ToastError
from .reports import labor_summary, sales_summary, transactions


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {value!r}") from None


def _resolve_window(args) -> tuple[datetime, datetime]:
    """Turn the mutually exclusive date flags into a concrete [start, end)."""
    if args.days is not None:
        end = datetime.now(timezone.utc)
        return end - timedelta(days=args.days), end
    if args.start and args.end:
        return args.start, args.end + timedelta(days=1)
    if args.start:
        return args.start, args.start + timedelta(days=1)
    # Default to yesterday, the usual "how did we do" question.
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return end - timedelta(days=1), end


def _add_window_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=_parse_date, help="Start date, YYYY-MM-DD (inclusive).")
    parser.add_argument("--end", type=_parse_date, help="End date, YYYY-MM-DD (inclusive).")
    parser.add_argument("--days", type=int, help="Look back this many days from now.")


def _json_default(value):
    if isinstance(value, Decimal):
        return float(round(value, 2))
    raise TypeError(f"not JSON serializable: {type(value)}")


def _dollars(value: Decimal) -> str:
    return f"${value:,.2f}"


# -- output ---------------------------------------------------------------


def _print_sales(summary: dict, label: str) -> None:
    print(f"\nSales — {label}")
    print("=" * (8 + len(label)))
    print(f"  Orders              {summary['orders']:>12,}")
    print(f"  Checks              {summary['checks']:>12,}")
    print(f"  Guests              {summary['guests']:>12,}")
    print(f"  Net sales           {_dollars(summary['net_sales']):>12}")
    print(f"  Tax                 {_dollars(summary['tax']):>12}")
    print(f"  Tips                {_dollars(summary['tips']):>12}")
    print(f"  Service charges     {_dollars(summary['service_charges']):>12}")
    print(f"  Discounts           {_dollars(summary['discounts']):>12}")
    print(f"  Refunds             {_dollars(summary['refunds']):>12}")
    print(f"  Total collected     {_dollars(summary['total_collected']):>12}")
    print(f"  Average check       {_dollars(summary['average_check']):>12}")
    if summary["voided_checks"]:
        print(f"  Voided checks       {summary['voided_checks']:>12,}")

    if summary["by_payment_type"]:
        print("\n  By payment type")
        for name, bucket in sorted(summary["by_payment_type"].items(), key=lambda kv: -kv[1]["amount"]):
            print(f"    {name:<18} {bucket['count']:>6,}  {_dollars(bucket['amount']):>12}  tips {_dollars(bucket['tips']):>10}")

    if summary["by_dining_option"]:
        print("\n  By dining option")
        for name, bucket in sorted(summary["by_dining_option"].items(), key=lambda kv: -kv[1]["net_sales"]):
            print(f"    {name:<18} {bucket['count']:>6,}  {_dollars(bucket['net_sales']):>12}")
    print()


def _print_labor(report: dict, label: str) -> None:
    totals = report["totals"]
    print(f"\nLabor — {label}")
    print("=" * (8 + len(label)))
    header = f"  {'Employee':<26}{'Shifts':>7}{'Reg hrs':>10}{'OT hrs':>9}{'Cash tips':>12}{'Card tips':>12}{'Est. pay':>12}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for row in report["employees"]:
        print(
            f"  {row['name'][:25]:<26}{row['shifts']:>7,}{row['regular_hours']:>10,.2f}"
            f"{row['overtime_hours']:>9,.2f}{_dollars(row['declared_cash_tips']):>12}"
            f"{_dollars(row['non_cash_tips']):>12}{_dollars(row['estimated_pay']):>12}"
        )
    print("  " + "-" * (len(header) - 2))
    print(
        f"  {'TOTAL':<26}{totals['shifts']:>7,}{totals['regular_hours']:>10,.2f}"
        f"{totals['overtime_hours']:>9,.2f}{_dollars(totals['declared_cash_tips']):>12}"
        f"{_dollars(totals['non_cash_tips']):>12}{_dollars(totals['estimated_pay']):>12}"
    )
    if totals["open_shifts"]:
        print(f"\n  {totals['open_shifts']} shift(s) still clocked in — hours are incomplete.")
    if totals["missed_breaks"]:
        print(f"  {totals['missed_breaks']} missed break(s) recorded.")
    print("\n  Estimated pay is hours x wage from the time clock. It is a labor-cost")
    print("  estimate, not a payroll run — no taxes, deductions, or salaried staff.\n")


def _write_csv(rows: list[dict]) -> None:
    if not rows:
        print("No rows.", file=sys.stderr)
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (f"{v:.2f}" if isinstance(v, Decimal) else v) for k, v in row.items()})


# -- commands -------------------------------------------------------------


def _cmd_check(client: ToastClient, args) -> int:
    restaurant = client.restaurant()
    general = restaurant.get("general") or {}
    print("Connected to Toast.")
    print(f"  Restaurant   {general.get('name') or restaurant.get('guid')}")
    print(f"  Location     {general.get('locationName') or '-'}")
    print(f"  Time zone    {general.get('timeZone') or '-'}")
    print(f"  Closeout     {general.get('closeoutHour')}:00")
    print(f"  GUID         {client.restaurant_guid}")
    return 0


def _cmd_sales(client: ToastClient, args) -> int:
    if args.business_date:
        label = args.business_date.strftime("%Y-%m-%d")
        orders = client.orders_for_business_date(args.business_date.strftime("%Y%m%d"))
    else:
        start, end = _resolve_window(args)
        label = f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
        orders = client.orders(start, end)

    summary = sales_summary(orders)
    if args.format == "json":
        print(json.dumps({"period": label, **summary}, default=_json_default, indent=2))
    else:
        _print_sales(summary, label)
    return 0


def _cmd_transactions(client: ToastClient, args) -> int:
    if args.business_date:
        orders = client.orders_for_business_date(args.business_date.strftime("%Y%m%d"))
    else:
        start, end = _resolve_window(args)
        orders = client.orders(start, end)

    rows = transactions(orders)
    if args.format == "json":
        print(json.dumps(rows, default=_json_default, indent=2))
    else:
        _write_csv(rows)
    return 0


def _cmd_labor(client: ToastClient, args) -> int:
    start, end = _resolve_window(args)
    label = f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"

    names: dict[str, str] = {}
    try:
        for employee in client.employees():
            first = employee.get("firstName") or ""
            last = employee.get("lastName") or ""
            full = f"{first} {last}".strip()
            if employee.get("guid") and full:
                names[employee["guid"]] = full
    except ToastError as exc:
        # Names are a nicety; without labor.employees:read the report still works.
        print(f"Note: could not load employee names ({exc}). Showing GUIDs.", file=sys.stderr)

    report = labor_summary(client.time_entries(start, end), names)
    if args.format == "json":
        print(json.dumps({"period": label, **report}, default=_json_default, indent=2))
    elif args.format == "csv":
        _write_csv(report["employees"])
    else:
        _print_labor(report, label)
    return 0


def _cmd_raw(client: ToastClient, args) -> int:
    params = dict(pair.split("=", 1) for pair in args.param)
    print(json.dumps(client.get(args.path, params), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="toast", description="Pull reports from the Toast API.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Verify credentials and show the connected restaurant.")
    check.set_defaults(func=_cmd_check)

    sales = sub.add_parser("sales", help="Sales summary for a period.")
    sales.add_argument("--business-date", type=_parse_date, help="One business day, YYYY-MM-DD.")
    _add_window_flags(sales)
    sales.add_argument("--format", choices=["table", "json"], default="table")
    sales.set_defaults(func=_cmd_sales)

    txns = sub.add_parser("transactions", help="One row per payment.")
    txns.add_argument("--business-date", type=_parse_date, help="One business day, YYYY-MM-DD.")
    _add_window_flags(txns)
    txns.add_argument("--format", choices=["csv", "json"], default="csv")
    txns.set_defaults(func=_cmd_transactions)

    labor = sub.add_parser("labor", help="Hours, tips, and estimated labor cost by employee.")
    _add_window_flags(labor)
    labor.add_argument("--format", choices=["table", "csv", "json"], default="table")
    labor.set_defaults(func=_cmd_labor)

    raw = sub.add_parser("raw", help="GET any Toast endpoint, for exploration.")
    raw.add_argument("path", help="e.g. /labor/v1/employees")
    raw.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    raw.set_defaults(func=_cmd_raw)

    args = parser.parse_args(argv)

    try:
        client = ToastClient()
        return args.func(client, args)
    except ToastError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if getattr(exc, "body", ""):
            print(exc.body[:2000], file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
