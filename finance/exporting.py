"""Shape the ledger into spreadsheet sheets.

Kept separate from excel.py so that module stays a general xlsx writer that
knows nothing about bank ledgers, and separate from cli.py so the dashboard
can embed the same workbook the `export` command writes — one definition of
what the export contains, used by both.
"""

from __future__ import annotations

from .analyse import GROUPINGS, Analysis
from .excel import Sheet
from .ledger import Ledger
from .reconcile import ReconciliationReport


def sheets_for(
    ledger: Ledger, analysis: Analysis, report: ReconciliationReport
) -> list[Sheet]:
    summary = [
        ["Period", f"{analysis.period_start} to {analysis.period_end}"],
        ["Transactions", len(ledger.transactions)],
        ["Opening balance", analysis.opening_balance],
        ["Total in", analysis.total_in],
        ["Total out", analysis.total_out],
        ["Net movement", analysis.net_movement],
        ["Closing balance", analysis.closing_balance],
        ["Lowest balance", analysis.trough],
        ["Lowest balance date", analysis.trough_date],
        ["Burn per month", analysis.burn_per_month],
        ["Unclassified rows", len(analysis.unclassified)],
        ["Reconciled", "yes" if report.ok else "NO — figures are provisional"],
    ]
    for item in report.discrepancies:
        summary.append([f"Discrepancy ({item.check})", item.message])
    for line in report.flagged:
        summary.append(["Flagged for review", line])

    sheets = [
        Sheet("Summary", ["Measure", "Value"], summary, [26, 70]),
        Sheet(
            "Transactions",
            ["Date", "Statement", "Branch", "Particulars", "Counterparty",
             "Instrument", "Reference", "Debit", "Credit", "Balance",
             "Category", "Needs review", "Note"],
            [[t.date, t.statement_id, t.branch, t.particulars, t.counterparty,
              t.instrument, t.reference, t.debit or None, t.credit or None,
              t.balance, t.label, "yes" if t.needs_review else "", t.note]
             for t in ledger.transactions],
            [12, 12, 12, 26, 14, 11, 11, 14, 14, 14, 20, 12, 40],
        ),
    ]

    for dimension in sorted(GROUPINGS):
        buckets = analysis.groups.get(dimension, [])
        if not buckets:
            continue
        sheets.append(
            Sheet(
                f"By {dimension}",
                [dimension.title(), "In", "Out", "Net", "Rows"],
                [[b.key, b.inflow or None, b.outflow or None, b.net, b.count]
                 for b in buckets],
                [26, 16, 16, 16, 8],
            )
        )

    if analysis.cheques:
        sheets.append(
            Sheet(
                "Cheque register",
                ["Cheque", "Date", "Amount", "Status"],
                [[c.reference, c.date, c.amount if c.presented else None,
                  "cleared" if c.presented else "never seen clearing"]
                 for c in analysis.cheques],
                [10, 12, 16, 24],
            )
        )
    return sheets
