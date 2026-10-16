"""Loading and validating the bank ledger.

The ledger is a CSV because it is diffable, auditable, editable without this
tool, and outlives it. Each row is one line on a bank statement: what the bank
said, not what we concluded. Derived values are never stored here — they are
recomputed on every run so the output is always reproducible from evidence.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from .money import ZERO, parse_money

# Cash-side classification. The accounting treatment is a separate decision —
# see .claude/skills/accountant — because a credit from a partner may be equity
# or a director loan, and the bank cannot tell you which.
CATEGORIES = {
    "opening_deposit": "Opening deposit",
    "transfer_in": "Transfer in",
    "cash_in": "Cash deposit",
    "cheque_in": "Cheque deposit",
    "cheque_out": "Cheque payment",
    "cash_cheque_out": "Counter-cash cheque",
    "transfer_cheque_out": "Transfer cheque",
    "bank_charge": "Bank charge",
    "other_in": "Other receipt",
    "other_out": "Other payment",
    # A row whose treatment has not been decided yet. Rows arrive this way from
    # a new statement and are resolved by `classify`. It is direction-agnostic
    # on purpose — you should not have to know what a payment was for in order
    # to record that it happened.
    "unclassified": "Unclassified",
}

INFLOW_CATEGORIES = {c for c in CATEGORIES if c.endswith("_in") or c == "opening_deposit"}

FIELDS = [
    "date",
    "statement_id",
    "branch",
    "particulars",
    "counterparty",
    "instrument",
    "reference",
    "debit",
    "credit",
    "balance",
    "category",
    "needs_review",
    "note",
]


class LedgerError(ValueError):
    """The ledger is malformed in a way that makes analysis meaningless."""


@dataclass(frozen=True)
class Transaction:
    date: date
    statement_id: str
    branch: str
    particulars: str
    counterparty: str
    instrument: str
    reference: str
    debit: Decimal
    credit: Decimal
    balance: Decimal
    category: str
    needs_review: bool
    note: str
    row_number: int = 0

    @property
    def amount(self) -> Decimal:
        """Signed movement: positive into the account, negative out of it."""
        return self.credit - self.debit

    @property
    def is_inflow(self) -> bool:
        return self.credit > ZERO

    @property
    def label(self) -> str:
        return CATEGORIES.get(self.category, self.category)


@dataclass(frozen=True)
class Statement:
    statement_id: str
    page_refs: str
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal


@dataclass
class Ledger:
    transactions: list[Transaction] = field(default_factory=list)
    statements: dict[str, Statement] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.transactions)

    @property
    def period(self) -> tuple[date, date] | None:
        if not self.transactions:
            return None
        dates = [t.date for t in self.transactions]
        return min(dates), max(dates)

    def for_statement(self, statement_id: str) -> list[Transaction]:
        return [t for t in self.transactions if t.statement_id == statement_id]


def _parse_date(raw: str, row_number: int) -> date:
    text = (raw or "").strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise LedgerError(f"row {row_number}: unreadable date {raw!r} (use YYYY-MM-DD)")


def _parse_flag(raw: str) -> bool:
    return (raw or "").strip().lower() in {"y", "yes", "true", "1"}


def load_transactions(path: Path | str) -> list[Transaction]:
    path = Path(path)
    if not path.exists():
        raise LedgerError(
            f"no ledger at {path}. Copy data/transactions.sample.csv to {path} "
            "and replace it with the real statement rows."
        )

    out: list[Transaction] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [f for f in FIELDS if f not in (reader.fieldnames or [])]
        if missing:
            raise LedgerError(f"{path}: missing column(s): {', '.join(missing)}")

        for offset, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue  # blank separator line

            debit = parse_money(row["debit"])
            credit = parse_money(row["credit"])
            if debit and credit:
                raise LedgerError(
                    f"row {offset}: has both a debit and a credit; a statement "
                    "line is one or the other"
                )
            if not debit and not credit:
                raise LedgerError(f"row {offset}: has neither a debit nor a credit")
            if debit < ZERO or credit < ZERO:
                raise LedgerError(
                    f"row {offset}: negative amount. Direction is the column, "
                    "not the sign — put outgoings in `debit`"
                )

            category = (row["category"] or "").strip()
            if category not in CATEGORIES:
                raise LedgerError(
                    f"row {offset}: unknown category {category!r}. "
                    f"Expected one of: {', '.join(sorted(CATEGORIES))}"
                )
            direction_in = category in INFLOW_CATEGORIES
            if category != "unclassified" and direction_in != bool(credit):
                raise LedgerError(
                    f"row {offset}: category {category!r} disagrees with the "
                    "amount column — an inflow category needs a credit"
                )

            out.append(
                Transaction(
                    date=_parse_date(row["date"], offset),
                    statement_id=(row["statement_id"] or "").strip(),
                    branch=(row["branch"] or "").strip(),
                    particulars=(row["particulars"] or "").strip(),
                    counterparty=(row["counterparty"] or "").strip(),
                    instrument=(row["instrument"] or "").strip(),
                    reference=(row["reference"] or "").strip(),
                    debit=debit,
                    credit=credit,
                    balance=parse_money(row["balance"]),
                    category=category,
                    needs_review=_parse_flag(row["needs_review"]),
                    note=(row["note"] or "").strip(),
                    row_number=offset,
                )
            )

    out.sort(key=lambda t: (t.date, t.row_number))
    return out


def load_statements(path: Path | str) -> dict[str, Statement]:
    path = Path(path)
    if not path.exists():
        return {}

    statements: dict[str, Statement] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for offset, row in enumerate(csv.DictReader(handle), start=2):
            if not (row.get("statement_id") or "").strip():
                continue
            statements[row["statement_id"].strip()] = Statement(
                statement_id=row["statement_id"].strip(),
                page_refs=(row.get("page_refs") or "").strip(),
                period_start=_parse_date(row["period_start"], offset),
                period_end=_parse_date(row["period_end"], offset),
                opening_balance=parse_money(row["opening_balance"]),
                closing_balance=parse_money(row["closing_balance"]),
                total_debits=parse_money(row["total_debits"]),
                total_credits=parse_money(row["total_credits"]),
            )
    return statements


def load(data_dir: Path | str = "data", *, sample_only: bool = False) -> Ledger:
    """Load the ledger, preferring real data and falling back to the sample.

    Pass sample_only=True to ignore the real ledger even when it is present.
    Tests use it so that their results never depend on whether this machine
    happens to hold private data.
    """
    data_dir = Path(data_dir)
    tx_path = data_dir / "transactions.csv"
    st_path = data_dir / "statements.csv"
    if sample_only or not tx_path.exists():
        tx_path = data_dir / "transactions.sample.csv"
        st_path = data_dir / "statements.sample.csv"
    return Ledger(
        transactions=load_transactions(tx_path),
        statements=load_statements(st_path),
    )
