"""Reconciliation: does the ledger agree with the bank?

Three independent checks. Each one can catch a mistake the others cannot, so
they are all worth running:

1. Running balance — every row's printed balance equals the previous balance
   plus the movement. Catches a mistyped amount on a single row.
2. Control totals — our debit and credit sums equal the totals the bank printed
   at the foot of the statement. Catches a whole row being dropped or
   duplicated, which check 1 cannot see.
3. Period continuity — each statement opens where the previous one closed.
   Catches a missing statement, which neither of the others can see.

An analysis built on an unreconciled ledger is confidently wrong, which is
worse than no analysis. So the CLI refuses to report on one without saying so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .ledger import Ledger
from .money import ZERO, fmt


@dataclass
class Discrepancy:
    check: str
    where: str
    expected: Decimal
    actual: Decimal
    message: str

    @property
    def difference(self) -> Decimal:
        return self.actual - self.expected


@dataclass
class ReconciliationReport:
    rows_checked: int = 0
    rows_agreeing: int = 0
    statements_checked: int = 0
    discrepancies: list[Discrepancy] = field(default_factory=list)
    flagged: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.discrepancies

    @property
    def summary(self) -> str:
        if self.ok:
            return (
                f"Reconciled: {self.rows_agreeing}/{self.rows_checked} rows and "
                f"{self.statements_checked} statement(s) agree with the bank."
            )
        return (
            f"NOT reconciled: {len(self.discrepancies)} discrepancy(ies) across "
            f"{self.rows_checked} rows."
        )


def reconcile(ledger: Ledger) -> ReconciliationReport:
    report = ReconciliationReport(rows_checked=len(ledger.transactions))

    # --- Check 1: running balance, per statement -------------------------
    for statement_id, statement in sorted(ledger.statements.items()):
        rows = ledger.for_statement(statement_id)
        if not rows:
            continue
        report.statements_checked += 1
        balance = statement.opening_balance
        for tx in rows:
            balance += tx.amount
            if balance == tx.balance:
                report.rows_agreeing += 1
            else:
                report.discrepancies.append(
                    Discrepancy(
                        check="running balance",
                        where=f"{tx.date} {tx.particulars} (row {tx.row_number})",
                        expected=balance,
                        actual=tx.balance,
                        message=(
                            f"computed {fmt(balance)} from the previous balance, "
                            f"but the row records {fmt(tx.balance)}"
                        ),
                    )
                )
                # Re-anchor so one bad row does not cascade into every later row.
                balance = tx.balance

        # --- Check 2: control totals -------------------------------------
        debits = sum((t.debit for t in rows), ZERO)
        credits = sum((t.credit for t in rows), ZERO)
        for label, ours, theirs in (
            ("debits", debits, statement.total_debits),
            ("credits", credits, statement.total_credits),
        ):
            if theirs and ours != theirs:
                report.discrepancies.append(
                    Discrepancy(
                        check="control total",
                        where=f"{statement_id} {label}",
                        expected=theirs,
                        actual=ours,
                        message=(
                            f"ledger totals {fmt(ours)} but the statement prints "
                            f"{fmt(theirs)} — a row is probably missing or duplicated"
                        ),
                    )
                )

        closing = statement.opening_balance + credits - debits
        if closing != statement.closing_balance:
            report.discrepancies.append(
                Discrepancy(
                    check="control total",
                    where=f"{statement_id} closing balance",
                    expected=statement.closing_balance,
                    actual=closing,
                    message=(
                        f"opening plus movement gives {fmt(closing)} but the "
                        f"statement closes at {fmt(statement.closing_balance)}"
                    ),
                )
            )

    # --- Check 3: period continuity --------------------------------------
    ordered = sorted(ledger.statements.values(), key=lambda s: s.period_start)
    for earlier, later in zip(ordered, ordered[1:]):
        if later.opening_balance != earlier.closing_balance:
            report.discrepancies.append(
                Discrepancy(
                    check="period continuity",
                    where=f"{earlier.statement_id} -> {later.statement_id}",
                    expected=earlier.closing_balance,
                    actual=later.opening_balance,
                    message=(
                        f"{earlier.statement_id} closes at "
                        f"{fmt(earlier.closing_balance)} on {earlier.period_end} but "
                        f"{later.statement_id} opens at {fmt(later.opening_balance)} "
                        f"on {later.period_start}. A statement covering the gap is "
                        "missing — obtain it from the bank rather than plugging the "
                        "difference."
                    ),
                )
            )

    report.flagged = [
        f"{t.date} {t.particulars}: {t.note or 'flagged for review'}"
        for t in ledger.transactions
        if t.needs_review
    ]
    return report
