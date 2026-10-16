"""Turning the ledger into the numbers a director asks about.

Read .claude/skills/financial-analyst before interpreting any of this. The
short version: inflows here are mostly partner funding, not revenue, so
anything that treats credits as sales is wrong.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .ledger import CATEGORIES, Ledger, Transaction
from .money import ZERO


@dataclass
class Bucket:
    """One slice of the ledger — a counterparty, a category, a month."""

    key: str
    inflow: Decimal = ZERO
    outflow: Decimal = ZERO
    count: int = 0

    @property
    def net(self) -> Decimal:
        return self.inflow - self.outflow


@dataclass
class ChequeEntry:
    reference: str
    number: int | None
    date: date | None
    amount: Decimal
    presented: bool


@dataclass
class Analysis:
    ledger: Ledger
    period_start: date | None = None
    period_end: date | None = None
    opening_balance: Decimal = ZERO
    closing_balance: Decimal = ZERO
    total_in: Decimal = ZERO
    total_out: Decimal = ZERO
    trough: Decimal = ZERO
    trough_date: date | None = None
    peak: Decimal = ZERO
    peak_date: date | None = None
    months_elapsed: Decimal = Decimal("0")
    by_counterparty: list[Bucket] = field(default_factory=list)
    by_category: list[Bucket] = field(default_factory=list)
    by_month: list[Bucket] = field(default_factory=list)
    balance_series: list[tuple[date, Decimal]] = field(default_factory=list)
    largest_out: list[Transaction] = field(default_factory=list)
    largest_in: list[Transaction] = field(default_factory=list)
    groups: dict[str, list[Bucket]] = field(default_factory=dict)
    unclassified: list[Transaction] = field(default_factory=list)
    cheques: list[ChequeEntry] = field(default_factory=list)
    repeated_amounts: list[tuple[Decimal, list[Transaction]]] = field(default_factory=list)

    @property
    def net_movement(self) -> Decimal:
        return self.total_in - self.total_out

    @property
    def burn_per_month(self) -> Decimal:
        """Average outflow per month. Blunt, but it is what runway rests on."""
        if self.months_elapsed <= 0:
            return ZERO
        return self.total_out / self.months_elapsed

    @property
    def days_of_cover(self) -> Decimal | None:
        """Days the closing balance would last at the average burn rate.

        None when there is no outflow to burn — a ratio with a zero
        denominator is not "infinite runway", it is "not enough data".
        """
        burn = self.burn_per_month
        if burn <= 0:
            return None
        return (self.closing_balance / burn) * Decimal(30)

    @property
    def outflow_concentration(self) -> Decimal:
        """Share of all outflow in the five largest payments.

        Averages hide this business: a handful of cheques dominate, so the
        mean payment size tells you almost nothing.
        """
        if self.total_out <= 0:
            return ZERO
        top = sum((t.debit for t in self.largest_out[:5]), ZERO)
        return (top / self.total_out) * Decimal(100)


def _month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _week_key(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year:04d}-W{week:02d}"


# The dimensions a ledger can be sliced by. Each entry is the key to group on
# and whether rows with no value for it still deserve a bucket: a payment with
# no identified counterparty should not quietly join one called "" and get
# counted as a person.
GROUPINGS: dict[str, tuple] = {
    "counterparty": (lambda t: t.counterparty, False),
    "category": (lambda t: CATEGORIES.get(t.category, t.category), True),
    "month": (lambda t: _month_key(t.date), True),
    "week": (lambda t: _week_key(t.date), True),
    "branch": (lambda t: t.branch, True),
    "instrument": (lambda t: t.instrument, True),
    "direction": (lambda t: "Money in" if t.is_inflow else "Money out", True),
}

# Dimensions whose keys are chronological, so they sort by key rather than size.
CHRONOLOGICAL = {"month", "week"}


def group(transactions: list[Transaction], dimension: str) -> list[Bucket]:
    """Bucket transactions by one dimension.

    Sorted by size for categorical dimensions (the biggest thing is what you
    want to see first) and by key for time ones (a month series out of
    chronological order is unreadable).
    """
    if dimension not in GROUPINGS:
        raise ValueError(
            f"unknown grouping {dimension!r}. Expected one of: "
            f"{', '.join(sorted(GROUPINGS))}"
        )
    keyfunc, include_blank = GROUPINGS[dimension]

    buckets: dict[str, Bucket] = {}
    for tx in transactions:
        key = keyfunc(tx) or ""
        if not key:
            if not include_blank:
                continue
            key = "(none recorded)"
        bucket = buckets.setdefault(key, Bucket(key=key))
        bucket.inflow += tx.credit
        bucket.outflow += tx.debit
        bucket.count += 1

    result = list(buckets.values())
    if dimension in CHRONOLOGICAL:
        return sorted(result, key=lambda b: b.key)
    return sorted(result, key=lambda b: b.inflow + b.outflow, reverse=True)


def analyse(ledger: Ledger, *, top_n: int = 8) -> Analysis:
    result = Analysis(ledger=ledger)
    transactions = ledger.transactions
    if not transactions:
        return result

    result.period_start = transactions[0].date
    result.period_end = transactions[-1].date

    statements = sorted(ledger.statements.values(), key=lambda s: s.period_start)
    result.opening_balance = statements[0].opening_balance if statements else ZERO
    result.closing_balance = transactions[-1].balance

    result.total_in = sum((t.credit for t in transactions), ZERO)
    result.total_out = sum((t.debit for t in transactions), ZERO)

    span_days = (result.period_end - result.period_start).days
    result.months_elapsed = Decimal(max(span_days, 1)) / Decimal("30.44")

    # Balance over time, plus the trough — the closing balance flatters the
    # real liquidity position, which is how far down it actually went.
    series: list[tuple[date, Decimal]] = []
    trough = peak = transactions[0].balance
    trough_date = peak_date = transactions[0].date
    for tx in transactions:
        series.append((tx.date, tx.balance))
        if tx.balance < trough:
            trough, trough_date = tx.balance, tx.date
        if tx.balance > peak:
            peak, peak_date = tx.balance, tx.date
    result.balance_series = series
    result.trough, result.trough_date = trough, trough_date
    result.peak, result.peak_date = peak, peak_date

    result.groups = {
        dimension: group(transactions, dimension) for dimension in GROUPINGS
    }
    result.by_counterparty = result.groups["counterparty"]
    result.by_category = result.groups["category"]
    result.by_month = result.groups["month"]
    result.unclassified = [t for t in transactions if t.category == "unclassified"]

    result.largest_out = sorted(
        (t for t in transactions if t.debit > 0), key=lambda t: t.debit, reverse=True
    )[:top_n]
    result.largest_in = sorted(
        (t for t in transactions if t.credit > 0), key=lambda t: t.credit, reverse=True
    )[:top_n]

    result.cheques = _cheque_register(transactions)
    result.repeated_amounts = _repeated_amounts(transactions)
    return result


def _cheque_register(transactions: list[Transaction]) -> list[ChequeEntry]:
    """Own cheques that cleared, plus the gaps in the numbering.

    A gap is a cheque number we have never seen clear. It is either unpresented
    (a real liability the bank balance does not show), cancelled, or on a
    statement we do not have. The register cannot tell which — it only says
    where to look, and the amount is unknown until someone checks the
    counterfoil.
    """
    issued: dict[int, Transaction] = {}
    for tx in transactions:
        if tx.category not in {"cheque_out", "cash_cheque_out", "transfer_cheque_out"}:
            continue
        reference = tx.reference.strip()
        # Own cheques are low sequential numbers; a long reference is an
        # inbound cheque drawn on someone else's account.
        if reference.isdigit() and len(reference) <= 4:
            issued[int(reference)] = tx

    if not issued:
        return []

    entries: list[ChequeEntry] = []
    for number in range(min(issued), max(issued) + 1):
        tx = issued.get(number)
        entries.append(
            ChequeEntry(
                reference=str(number),
                number=number,
                date=tx.date if tx else None,
                amount=tx.debit if tx else ZERO,
                presented=tx is not None,
            )
        )
    return entries


def _repeated_amounts(
    transactions: list[Transaction], *, threshold: Decimal = Decimal("100000")
) -> list[tuple[Decimal, list[Transaction]]]:
    """Identical large amounts appearing more than once.

    Usually a standing commitment paid repeatedly — worth knowing about.
    Occasionally a double payment or a transcription error. Either way it is
    something to look at rather than something the tool should decide about.
    """
    groups: dict[Decimal, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        amount = tx.debit or tx.credit
        if amount >= threshold:
            groups[amount].append(tx)
    repeated = [(amount, txs) for amount, txs in groups.items() if len(txs) > 1]
    return sorted(repeated, key=lambda pair: pair[0], reverse=True)
