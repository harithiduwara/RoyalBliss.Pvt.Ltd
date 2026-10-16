"""Command line for the Royal Bliss cash tracker.

    python -m finance.cli check              reconcile against the bank
    python -m finance.cli analyse            print the cash summary
    python -m finance.cli add [...]          append a transaction
    python -m finance.cli classify           apply classification rules
    python -m finance.cli export             write an .xlsx workbook
    python -m finance.cli report             render the HTML dashboard
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from .analyse import GROUPINGS, analyse, group
from .ledger import CATEGORIES, FIELDS, INFLOW_CATEGORIES, LedgerError, load, load_transactions
from .money import ZERO, fmt, fmt_short, parse_money
from .reconcile import reconcile
from .rules import Change, Rule, apply_changes, load_rules, plan

DATA_DIR = Path("data")
OUTPUT_DIR = Path("build-finance")

RULE = "─" * 72


def _ledger_path(data_dir: Path) -> Path:
    real = data_dir / "transactions.csv"
    return real if real.exists() else data_dir / "transactions.sample.csv"


def _print_reconciliation(report, *, verbose: bool = True) -> None:
    print(report.summary)
    if report.discrepancies:
        print()
        for item in report.discrepancies:
            print(f"  [{item.check}] {item.where}")
            print(f"      {item.message}")
            print(f"      difference: {fmt(item.difference)}")
    if report.flagged and verbose:
        print(f"\n  {len(report.flagged)} row(s) flagged for human review:")
        for line in report.flagged:
            print(f"      {line}")


def cmd_check(args) -> int:
    ledger = load(args.data_dir)
    report = reconcile(ledger)
    print(f"Ledger: {_ledger_path(args.data_dir)}  ({len(ledger)} transactions)")
    print(RULE)
    _print_reconciliation(report)
    return 0 if report.ok else 1


def cmd_analyse(args) -> int:
    ledger = load(args.data_dir)
    report = reconcile(ledger)
    result = analyse(ledger)

    print(f"ROYAL BLISS (PVT) LTD — cash position        all amounts LKR")
    print(RULE)
    if result.period_start:
        print(f"Period      {result.period_start} to {result.period_end}")
    print(f"Ledger      {_ledger_path(args.data_dir)}  ({len(ledger)} transactions)")
    print()
    _print_reconciliation(report, verbose=False)
    if not report.ok:
        print("\n  ⚠ Figures below span an unreconciled ledger — treat as provisional.")
    print(RULE)

    rows = [
        ("Opening balance", fmt(result.opening_balance)),
        ("Total in", fmt(result.total_in)),
        ("Total out", fmt(result.total_out)),
        ("Net movement", fmt(result.net_movement)),
        ("Closing balance", fmt(result.closing_balance)),
        ("Lowest balance", f"{fmt(result.trough)}  on {result.trough_date}"),
        ("Burn (per month)", fmt(result.burn_per_month)),
    ]
    cover = result.days_of_cover
    rows.append(
        ("Days of cover", f"{cover:.0f}" if cover is not None else "n/a (no outflow)")
    )
    rows.append(("Top 5 payments", f"{result.outflow_concentration:.1f}% of all outflow"))
    for label, value in rows:
        print(f"  {label:<20} {value:>24}")

    def table(title: str, buckets, limit: int = 10) -> None:
        if not buckets:
            return
        print(f"\n  {title}")
        print(f"  {'':<22}{'in':>16}{'out':>16}{'net':>16}")
        for bucket in buckets[:limit]:
            print(
                f"  {bucket.key[:22]:<22}{fmt(bucket.inflow):>16}"
                f"{fmt(bucket.outflow):>16}{fmt(bucket.net):>16}"
            )

    for dimension in args.group_by:
        label = {
            "counterparty": "Funding and payments by counterparty",
            "category": "By category",
            "month": "By month",
            "week": "By week",
            "branch": "By branch or channel",
            "instrument": "By instrument",
            "direction": "By direction",
        }[dimension]
        table(label, result.groups[dimension], limit=30)

    if result.unclassified:
        print(
            f"\n  {len(result.unclassified)} row(s) still unclassified. "
            "Run `classify` to apply the rules in data/rules.csv."
        )

    if result.largest_out:
        print("\n  Largest payments")
        for tx in result.largest_out[:5]:
            print(f"  {tx.date}  {fmt(tx.debit):>16}  {tx.particulars[:34]}")

    unpresented = [c for c in result.cheques if not c.presented]
    if unpresented:
        numbers = ", ".join(c.reference for c in unpresented)
        print(
            f"\n  Cheque numbers never seen clearing: {numbers}"
            "\n  Each is unpresented, cancelled, or on a statement we do not have."
            "\n  Amounts are unknown until someone checks the counterfoils."
        )
    return 0 if report.ok else 1


def cmd_add(args) -> int:
    path = args.data_dir / "transactions.csv"
    if not path.exists():
        print(
            f"No {path} yet. Copy data/transactions.sample.csv to it first so the "
            "real ledger stays separate from the committed example.",
            file=sys.stderr,
        )
        return 2

    if args.category not in CATEGORIES:
        print(
            f"Unknown category {args.category!r}. Expected one of: "
            f"{', '.join(sorted(CATEGORIES))}",
            file=sys.stderr,
        )
        return 2

    amount = parse_money(args.amount)
    if amount <= ZERO:
        print("Amount must be positive — direction comes from the category.", file=sys.stderr)
        return 2

    inflow = args.category in INFLOW_CATEGORIES
    existing = load_transactions(path)
    previous = existing[-1].balance if existing else ZERO
    balance = previous + amount if inflow else previous - amount

    row = {
        "date": args.date,
        "statement_id": args.statement or "",
        "branch": args.branch or "",
        "particulars": args.particulars,
        "counterparty": args.counterparty or "",
        "instrument": args.instrument or "",
        "reference": args.reference or "",
        "debit": "" if inflow else f"{amount:.2f}",
        "credit": f"{amount:.2f}" if inflow else "",
        "balance": f"{balance:.2f}",
        "category": args.category,
        "needs_review": "yes" if args.needs_review else "",
        "note": args.note or "",
    }

    with path.open("a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS).writerow(row)

    direction = "in" if inflow else "out"
    print(f"Added {args.date}  {fmt(amount)} {direction}  {args.particulars}")
    print(f"Running balance now {fmt(balance)}")
    print(
        "\nThis balance is computed, not the bank's. Replace it with the printed "
        "balance when the statement arrives, then run `check`."
    )
    return 0


def cmd_classify(args) -> int:
    """Apply classification rules. Shows the diff first; writes only on --apply."""
    path = _ledger_path(args.data_dir)
    transactions = load_transactions(path)

    if args.row is not None:
        # A manual override is the one case that needs no rules file at all.
        # Manual override for one row, for the cases no rule should encode.
        target = next((t for t in transactions if t.row_number == args.row), None)
        if target is None:
            print(f"No row {args.row} in {path}.", file=sys.stderr)
            return 2
        if args.category and args.category not in CATEGORIES:
            print(f"Unknown category {args.category!r}.", file=sys.stderr)
            return 2
        # The same guard the rules engine applies: the bank decides whether a
        # row is money in or out, and no manual override gets to contradict it.
        # Without this you can write a ledger that will not load next time.
        if args.category and args.category != "unclassified":
            if (args.category in INFLOW_CATEGORIES) != target.is_inflow:
                print(
                    f"Row {args.row} is money {'in' if target.is_inflow else 'out'} "
                    f"({fmt(target.credit or target.debit)}), so it cannot be "
                    f"{args.category!r}. Pick a category on the same side.",
                    file=sys.stderr,
                )
                return 2
        manual = Rule("any", "", args.category or "", args.counterparty or "", "manual")
        change = Change(target, manual, args.category or None, args.counterparty or None)
        print(f"row {args.row}  {target.date}  {target.particulars}")
        print(f"  {change.describe()}")
        if not args.apply:
            print("\nNothing written. Re-run with --apply to save.")
            return 0
        apply_changes(path, [change])
        print("\nSaved.")
        return 0

    rules_path = args.rules or (args.data_dir / "rules.csv")
    if not Path(rules_path).exists():
        fallback = args.data_dir / "rules.sample.csv"
        if not fallback.exists():
            print(
                f"No rules file at {rules_path}. Copy data/rules.sample.csv to it "
                "and edit it, or classify one row at a time with --row.",
                file=sys.stderr,
            )
            return 2
        rules_path = fallback
        print(f"No {args.data_dir / 'rules.csv'} — using the sample rules instead.\n")

    rules = load_rules(rules_path)
    changes, warnings = plan(transactions, rules, reclassify_all=args.all)

    print(f"Ledger: {path}  ({len(transactions)} transactions)")
    print(f"Rules:  {rules_path}  ({len(rules)} rules)")
    print(RULE)
    if warnings:
        print("Rules that could not be applied:")
        for warning in warnings:
            print(f"  ! {warning}")
        print()
    if not changes:
        print("No changes — every row already matches the rules.")
        return 0

    print(f"{len(changes)} row(s) would change:\n")
    for change in changes[:40]:
        tx = change.transaction
        print(f"  row {tx.row_number:>3}  {tx.date}  {tx.particulars[:30]:<30} {change.describe()}")
    if len(changes) > 40:
        print(f"  … and {len(changes) - 40} more")

    if not args.apply:
        print("\nNothing written. Re-run with --apply to save these to the ledger.")
        return 0

    written = apply_changes(path, changes)
    print(f"\nSaved {written} row(s) to {path}.")
    print("Run `check` to confirm the ledger still reconciles.")
    return 0


def cmd_export(args) -> int:
    from .excel import write_workbook
    from .exporting import sheets_for

    ledger = load(args.data_dir)
    report = reconcile(ledger)
    result = analyse(ledger)

    write_workbook(args.output, sheets_for(ledger, result, report))
    print(f"Workbook written to {args.output}")
    if not report.ok:
        print("⚠ The ledger does not reconcile — the Summary sheet says why.")
    print(
        "\nContains company bank data. Written to a git-ignored directory on "
        "purpose — do not commit it."
    )
    return 0 if report.ok else 1


def cmd_report(args) -> int:
    from .report import render  # imported here so `check` has no HTML dependency

    ledger = load(args.data_dir)
    report = reconcile(ledger)
    result = analyse(ledger)

    workbook = None
    if not args.no_excel:
        from .excel import build_workbook
        from .exporting import sheets_for

        workbook = build_workbook(sheets_for(ledger, result, report))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(result, report, workbook), encoding="utf-8")

    print(f"Dashboard written to {args.output}")
    print(_ledger_path(args.data_dir).name, f"— {len(ledger)} transactions")
    if not report.ok:
        print(f"⚠ {len(report.discrepancies)} reconciliation discrepancy(ies) shown at the top.")
    print(
        "\nThis file contains company bank data. It is written to a git-ignored "
        "directory on purpose — do not commit it or publish it."
    )
    return 0 if report.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finance", description="Royal Bliss cash tracker (local use only)"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=DATA_DIR, help="where the ledger CSVs live"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="reconcile the ledger against the bank").set_defaults(
        func=cmd_check
    )
    ana = sub.add_parser("analyse", help="print the cash summary")
    ana.add_argument(
        "--group-by", nargs="+", choices=sorted(GROUPINGS),
        default=["counterparty", "category", "month"],
        help="dimensions to break the totals down by",
    )
    ana.set_defaults(func=cmd_analyse)

    cls = sub.add_parser("classify", help="apply classification rules to the ledger")
    cls.add_argument("--rules", type=Path, help="rules file (default data/rules.csv)")
    cls.add_argument("--apply", action="store_true", help="write the changes (default: preview only)")
    cls.add_argument("--all", action="store_true", help="also reclassify rows that already have a category")
    cls.add_argument("--row", type=int, help="classify one row by its line number instead of using rules")
    cls.add_argument("--category", choices=sorted(CATEGORIES), help="category for --row")
    cls.add_argument("--counterparty", help="counterparty for --row")
    cls.set_defaults(func=cmd_classify)

    exp = sub.add_parser("export", help="export the ledger and groupings to .xlsx")
    exp.add_argument("--output", type=Path, default=OUTPUT_DIR / "royal-bliss-cash.xlsx")
    exp.set_defaults(func=cmd_export)

    add = sub.add_parser("add", help="append a transaction to the ledger")
    add.add_argument("--date", required=True, help="YYYY-MM-DD")
    add.add_argument("--amount", required=True, help="positive amount, e.g. 150000.00")
    add.add_argument("--category", required=True, choices=sorted(CATEGORIES))
    add.add_argument("--particulars", required=True, help="as printed on the statement")
    add.add_argument("--counterparty", default="")
    add.add_argument("--branch", default="")
    add.add_argument("--instrument", default="")
    add.add_argument("--reference", default="", help="cheque number, if any")
    add.add_argument("--statement", default="", help="statement id")
    add.add_argument("--note", default="")
    add.add_argument("--needs-review", action="store_true")
    add.set_defaults(func=cmd_add)

    rep = sub.add_parser("report", help="render the HTML dashboard")
    rep.add_argument("--output", type=Path, default=OUTPUT_DIR / "index.html")
    rep.add_argument(
        "--no-excel", action="store_true",
        help="skip the embedded workbook (smaller file, no download button)",
    )
    rep.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LedgerError as exc:
        print(f"Ledger problem: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
