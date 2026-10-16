"""Money handling.

Every amount in this package is a Decimal. The ledger reconciles to the cent
against the bank's printed control totals, and binary floating point breaks
that silently — 0.1 + 0.2 != 0.3 — so a float would turn an exact check into
an approximate one without anyone noticing.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def parse_money(raw: str | Decimal | int | None) -> Decimal:
    """Read an amount from a CSV cell.

    Blank means "no amount on this side of the ledger", which is zero — a bank
    statement leaves the debit column empty on a credit row.
    """
    if raw is None:
        return ZERO
    if isinstance(raw, Decimal):
        return raw
    if isinstance(raw, int):
        return Decimal(raw)

    text = str(raw).strip().replace(",", "")
    if not text:
        return ZERO
    # Statements print credit balances as "1,234.56Cr"; the Cr is the sign
    # convention for the column, not part of the number.
    if text.lower().endswith("cr"):
        text = text[:-2].strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"not a valid amount: {raw!r}") from exc


def fmt(amount: Decimal, *, places: int = 2) -> str:
    """Format for a table: thousands separators, fixed decimals, no currency."""
    quantised = Decimal(amount).quantize(Decimal(10) ** -places)
    return f"{quantised:,.{places}f}"


def fmt_short(amount: Decimal) -> str:
    """Format for a headline tile: 3.14M, 905.2K, 412.

    Only ever use this in prose and KPI tiles. A table someone reconciles
    against a bank statement needs every digit.
    """
    value = Decimal(amount)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:,.2f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:,.1f}K"
    return f"{sign}{value:,.0f}"
