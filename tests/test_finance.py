"""Tests for the cash tracker.

The important ones are the reconciliation tests: they are what stop a silently
wrong ledger from reaching a dashboard someone trusts.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance.analyse import analyse
from finance.ledger import FIELDS, LedgerError, load, load_transactions
from finance.money import fmt, fmt_short, parse_money
from finance.reconcile import reconcile

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def sample():
    # sample_only: never read the real ledger, even on a machine that has one.
    return load(DATA, sample_only=True)


def write_ledger(tmp_path: Path, rows: list[dict], statements: list[dict] | None = None) -> Path:
    tx = tmp_path / "transactions.csv"
    with tx.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    if statements is not None:
        st = tmp_path / "statements.csv"
        with st.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "statement_id", "page_refs", "period_start", "period_end",
                    "opening_balance", "closing_balance", "total_debits", "total_credits",
                ],
            )
            writer.writeheader()
            writer.writerows(statements)
    return tmp_path


def row(**kwargs) -> dict:
    base = {
        "date": "2026-01-01", "statement_id": "S1", "branch": "B",
        "particulars": "test", "category": "transfer_in", "credit": "100.00",
        "balance": "100.00",
    }
    base.update(kwargs)
    return base


# --- money ------------------------------------------------------------

def test_parse_money_handles_statement_formats():
    assert parse_money("1,280,852.12") == Decimal("1280852.12")
    assert parse_money("3,142,657.15Cr") == Decimal("3142657.15")
    assert parse_money("") == Decimal("0.00")
    assert parse_money(None) == Decimal("0.00")


def test_parse_money_rejects_nonsense():
    with pytest.raises(ValueError):
        parse_money("about fifty")


def test_amounts_stay_exact():
    """The whole package depends on this; floats would make it false."""
    total = sum(parse_money(x) for x in ["0.10", "0.20"])
    assert total == Decimal("0.30")


def test_formatting():
    assert fmt(Decimal("1280852.1")) == "1,280,852.10"
    assert fmt_short(Decimal("3142657.15")) == "3.14M"
    assert fmt_short(Decimal("-905200")) == "-905.2K"


# --- ledger validation -------------------------------------------------

def test_sample_ledger_loads(sample):
    assert len(sample) == 11
    assert sample.period == (date(2026, 1, 5), date(2026, 2, 28))


def test_rejects_row_with_both_debit_and_credit(tmp_path):
    write_ledger(tmp_path, [row(debit="50.00", credit="100.00")])
    with pytest.raises(LedgerError, match="both a debit and a credit"):
        load_transactions(tmp_path / "transactions.csv")


def test_rejects_row_with_neither(tmp_path):
    write_ledger(tmp_path, [row(credit="")])
    with pytest.raises(LedgerError, match="neither a debit nor a credit"):
        load_transactions(tmp_path / "transactions.csv")


def test_rejects_negative_amount(tmp_path):
    write_ledger(tmp_path, [row(credit="-100.00")])
    with pytest.raises(LedgerError, match="negative amount"):
        load_transactions(tmp_path / "transactions.csv")


def test_rejects_unknown_category(tmp_path):
    write_ledger(tmp_path, [row(category="vibes")])
    with pytest.raises(LedgerError, match="unknown category"):
        load_transactions(tmp_path / "transactions.csv")


def test_rejects_category_contradicting_direction(tmp_path):
    """An outflow category on a credit row means someone mis-keyed it."""
    write_ledger(tmp_path, [row(category="cheque_out", credit="100.00")])
    with pytest.raises(LedgerError, match="disagrees with the amount column"):
        load_transactions(tmp_path / "transactions.csv")


def test_missing_ledger_explains_what_to_do(tmp_path):
    with pytest.raises(LedgerError, match="sample"):
        load_transactions(tmp_path / "nothing.csv")


# --- reconciliation ----------------------------------------------------

def test_sample_reconciles(sample):
    report = reconcile(sample)
    assert report.ok, [d.message for d in report.discrepancies]
    assert report.rows_agreeing == 11


def test_detects_wrong_running_balance(tmp_path):
    base = write_ledger(
        tmp_path,
        [
            row(date="2026-01-01", credit="100.00", balance="100.00"),
            row(date="2026-01-02", credit="100.00", balance="999.00"),
        ],
        [{
            "statement_id": "S1", "page_refs": "", "period_start": "2026-01-01",
            "period_end": "2026-01-02", "opening_balance": "0.00",
            "closing_balance": "200.00", "total_debits": "0.00",
            "total_credits": "200.00",
        }],
    )
    report = reconcile(load(base))
    assert not report.ok
    assert any(d.check == "running balance" for d in report.discrepancies)


def test_detects_dropped_row_via_control_totals(tmp_path):
    """A missing row keeps the running balance self-consistent, so only the
    bank's printed totals can catch it."""
    base = write_ledger(
        tmp_path,
        [row(date="2026-01-01", credit="100.00", balance="100.00")],
        [{
            "statement_id": "S1", "page_refs": "", "period_start": "2026-01-01",
            "period_end": "2026-01-31", "opening_balance": "0.00",
            "closing_balance": "100.00", "total_debits": "0.00",
            "total_credits": "250.00",
        }],
    )
    report = reconcile(load(base))
    assert any(d.check == "control total" for d in report.discrepancies)


def test_detects_missing_statement_between_periods(tmp_path):
    base = write_ledger(
        tmp_path,
        [
            row(date="2026-01-01", statement_id="S1", credit="100.00", balance="100.00"),
            row(date="2026-02-01", statement_id="S2", credit="50.00", balance="950.00"),
        ],
        [
            {"statement_id": "S1", "page_refs": "", "period_start": "2026-01-01",
             "period_end": "2026-01-31", "opening_balance": "0.00",
             "closing_balance": "100.00", "total_debits": "0.00", "total_credits": "100.00"},
            {"statement_id": "S2", "page_refs": "", "period_start": "2026-02-01",
             "period_end": "2026-02-28", "opening_balance": "900.00",
             "closing_balance": "950.00", "total_debits": "0.00", "total_credits": "50.00"},
        ],
    )
    report = reconcile(load(base))
    gaps = [d for d in report.discrepancies if d.check == "period continuity"]
    assert len(gaps) == 1
    assert gaps[0].difference == Decimal("800.00")


def test_one_bad_row_does_not_cascade(tmp_path):
    """Re-anchoring after a break means the report names one bad row, not
    every row after it — otherwise a single typo buries the real signal."""
    base = write_ledger(
        tmp_path,
        [
            row(date="2026-01-01", credit="100.00", balance="100.00"),
            row(date="2026-01-02", credit="100.00", balance="999.00"),
            row(date="2026-01-03", credit="100.00", balance="1099.00"),
        ],
        [{"statement_id": "S1", "page_refs": "", "period_start": "2026-01-01",
          "period_end": "2026-01-31", "opening_balance": "0.00",
          "closing_balance": "1099.00", "total_debits": "0.00",
          "total_credits": "300.00"}],
    )
    report = reconcile(load(base))
    balance_breaks = [d for d in report.discrepancies if d.check == "running balance"]
    assert len(balance_breaks) == 1


def test_flags_rows_marked_for_review(sample):
    report = reconcile(sample)
    assert any("CACHQ 2" in line for line in report.flagged)


# --- analysis ----------------------------------------------------------

def test_totals(sample):
    result = analyse(sample)
    assert result.total_in == Decimal("1285000.00")
    assert result.total_out == Decimal("1085000.00")
    assert result.net_movement == Decimal("200000.00")
    assert result.closing_balance == Decimal("200000.00")


def test_trough_is_lower_than_closing_balance(sample):
    """The point of tracking the trough: the closing balance hides the dip."""
    result = analyse(sample)
    assert result.trough == Decimal("48500.00")
    assert result.trough < result.closing_balance


def test_counterparty_funding_is_grouped(sample):
    result = analyse(sample)
    by_name = {b.key: b for b in result.by_counterparty}
    assert by_name["Partner A"].inflow == Decimal("550000.00")
    assert by_name["Partner B"].inflow == Decimal("250000.00")
    assert "" not in by_name


def test_months_are_ordered(sample):
    result = analyse(sample)
    assert [b.key for b in result.by_month] == ["2026-01", "2026-02"]


def test_cheque_register_reports_gaps(sample):
    """Cheques 1, 2, 4 and 5 cleared; 3 never did and must be chased."""
    result = analyse(sample)
    unpresented = [c.reference for c in result.cheques if not c.presented]
    assert unpresented == ["3"]


def test_cheque_register_ignores_inbound_cheques(sample):
    """455001 is drawn on someone else's account, not one of ours."""
    result = analyse(sample)
    assert all(c.reference != "455001" for c in result.cheques)


def test_days_of_cover_is_none_without_outflow(tmp_path):
    base = write_ledger(
        tmp_path,
        [row(date="2026-01-01", credit="100.00", balance="100.00")],
        [{"statement_id": "S1", "page_refs": "", "period_start": "2026-01-01",
          "period_end": "2026-01-31", "opening_balance": "0.00",
          "closing_balance": "100.00", "total_debits": "0.00",
          "total_credits": "100.00"}],
    )
    assert analyse(load(base)).days_of_cover is None


def test_empty_ledger_does_not_crash(tmp_path):
    base = write_ledger(tmp_path, [], [])
    result = analyse(load(base))
    assert result.total_in == Decimal("0.00")
    assert result.balance_series == []
