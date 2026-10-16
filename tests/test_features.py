"""Tests for classification, grouping and the spreadsheet export."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree

import pytest

from finance.analyse import GROUPINGS, analyse, group
from finance.excel import Sheet, build_workbook
from finance.exporting import sheets_for
from finance.ledger import FIELDS, LedgerError, Transaction, load, load_transactions
from finance.reconcile import reconcile
from finance.report import render
from finance.rules import apply_changes, load_rules, plan

DATA = Path(__file__).resolve().parent.parent / "data"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


@pytest.fixture
def sample():
    return load(DATA, sample_only=True)


def tx(**kwargs) -> Transaction:
    base = dict(
        date=date(2026, 1, 1), statement_id="S1", branch="KIRULAPO",
        particulars="VSRTFR-Harith In", counterparty="", instrument="VSRTFR",
        reference="", debit=Decimal("0"), credit=Decimal("100"),
        balance=Decimal("100"), category="unclassified", needs_review=False,
        note="", row_number=2,
    )
    base.update(kwargs)
    return Transaction(**base)


def write_rules(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "rules.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["match_field", "pattern", "category", "counterparty", "note"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


# --- grouping ----------------------------------------------------------

@pytest.mark.parametrize("dimension", sorted(GROUPINGS))
def test_every_dimension_groups(sample, dimension):
    buckets = group(sample.transactions, dimension)
    assert buckets
    assert all(b.count > 0 for b in buckets)


def test_every_grouping_totals_the_same(sample):
    """Different cuts of the same ledger must agree, or one of them is lying."""
    totals = {
        dimension: (
            sum(b.inflow for b in group(sample.transactions, dimension)),
            sum(b.outflow for b in group(sample.transactions, dimension)),
        )
        for dimension in GROUPINGS
        if dimension != "counterparty"  # excludes unnamed rows by design
    }
    assert len(set(totals.values())) == 1, totals


def test_time_dimensions_sort_chronologically(sample):
    keys = [b.key for b in group(sample.transactions, "month")]
    assert keys == sorted(keys)


def test_categorical_dimensions_sort_by_size(sample):
    sizes = [b.inflow + b.outflow for b in group(sample.transactions, "branch")]
    assert sizes == sorted(sizes, reverse=True)


def test_counterparty_drops_unnamed_rows(sample):
    """A payment with no named counterparty must not become a person."""
    keys = [b.key for b in group(sample.transactions, "counterparty")]
    assert "" not in keys and "(none recorded)" not in keys


def test_blank_keys_are_labelled_not_empty(sample):
    keys = [b.key for b in group(sample.transactions, "instrument")]
    assert all(k.strip() for k in keys)


def test_unknown_dimension_is_rejected(sample):
    with pytest.raises(ValueError, match="unknown grouping"):
        group(sample.transactions, "vibes")


# --- classification ----------------------------------------------------

def test_substring_rule_matches_case_insensitively(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "particulars", "pattern": "harith", "category": "transfer_in",
         "counterparty": "Harith", "note": ""},
    ]))
    changes, warnings = plan([tx()], rules)
    assert not warnings
    assert changes[0].category == "transfer_in"
    assert changes[0].counterparty == "Harith"


def test_regex_rule(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "particulars", "pattern": "re:^VSRTFR", "category": "transfer_in",
         "counterparty": "", "note": ""},
    ]))
    changes, _ = plan([tx()], rules)
    assert changes[0].category == "transfer_in"


def test_bad_regex_is_reported_with_its_line(tmp_path):
    path = write_rules(tmp_path, [
        {"match_field": "particulars", "pattern": "re:[unclosed", "category": "",
         "counterparty": "X", "note": ""},
    ])
    with pytest.raises(LedgerError, match="line 2"):
        load_rules(path)


def test_unknown_category_in_rules_is_rejected(tmp_path):
    path = write_rules(tmp_path, [
        {"match_field": "any", "pattern": "x", "category": "nonsense",
         "counterparty": "", "note": ""},
    ])
    with pytest.raises(LedgerError, match="unknown category"):
        load_rules(path)


def test_rule_cannot_flip_a_payment_into_a_receipt(tmp_path):
    """The bank decides direction. A rule that disagrees is skipped, not obeyed."""
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "VSRTFR", "category": "cheque_out",
         "counterparty": "", "note": ""},
    ]))
    changes, warnings = plan([tx()], rules)
    assert changes == []
    assert len(warnings) == 1
    assert "money in" in warnings[0]


def test_first_matching_rule_wins(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "VSRTFR", "category": "transfer_in",
         "counterparty": "First", "note": ""},
        {"match_field": "any", "pattern": "Harith", "category": "cash_in",
         "counterparty": "Second", "note": ""},
    ]))
    changes, _ = plan([tx()], rules)
    assert changes[0].counterparty == "First"


def test_settled_rows_are_left_alone(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "VSRTFR", "category": "cash_in",
         "counterparty": "", "note": ""},
    ]))
    changes, _ = plan([tx(category="transfer_in", counterparty="Harith")], rules)
    assert changes == []


def test_blank_counterparty_is_filled_even_on_settled_rows(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "VSRTFR", "category": "",
         "counterparty": "Harith", "note": ""},
    ]))
    changes, _ = plan([tx(category="transfer_in", counterparty="")], rules)
    assert changes[0].counterparty == "Harith"
    assert changes[0].category is None


def test_reclassify_all_revisits_settled_rows(tmp_path):
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "VSRTFR", "category": "cash_in",
         "counterparty": "", "note": ""},
    ]))
    changes, _ = plan([tx(category="transfer_in")], rules, reclassify_all=True)
    assert changes[0].category == "cash_in"


def test_apply_changes_writes_only_the_matched_columns(tmp_path):
    path = tmp_path / "transactions.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({
            "date": "2026-01-01", "statement_id": "S1", "branch": "B",
            "particulars": "VSRTFR-Harith", "counterparty": "", "instrument": "VSRTFR",
            "reference": "", "debit": "", "credit": "100.00", "balance": "100.00",
            "category": "unclassified", "needs_review": "", "note": "keep me",
        })
    rules = load_rules(write_rules(tmp_path, [
        {"match_field": "any", "pattern": "Harith", "category": "transfer_in",
         "counterparty": "Harith", "note": ""},
    ]))
    changes, _ = plan(load_transactions(path), rules)
    assert apply_changes(path, changes) == 1

    after = load_transactions(path)[0]
    assert after.category == "transfer_in"
    assert after.counterparty == "Harith"
    assert after.note == "keep me"
    assert after.balance == Decimal("100.00")


def test_unclassified_rows_survive_loading_and_are_surfaced(tmp_path):
    path = tmp_path / "transactions.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({
            "date": "2026-01-01", "statement_id": "S1", "branch": "B",
            "particulars": "mystery", "counterparty": "", "instrument": "",
            "reference": "", "debit": "50.00", "credit": "", "balance": "-50.00",
            "category": "unclassified", "needs_review": "", "note": "",
        })
    result = analyse(load(tmp_path))
    assert len(result.unclassified) == 1


# --- excel -------------------------------------------------------------

def test_workbook_is_a_valid_zip_with_the_required_parts():
    data = build_workbook([Sheet("One", ["A"], [["x"]])])
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    for required in ("[Content_Types].xml", "_rels/.rels", "xl/workbook.xml",
                     "xl/styles.xml", "xl/worksheets/sheet1.xml"):
        assert required in names


def test_numbers_and_dates_are_typed_not_stringified():
    """A spreadsheet whose amounts are text cannot be summed, which defeats
    the point of exporting one."""
    data = build_workbook([
        Sheet("S", ["Date", "Amount"], [[date(2026, 9, 28), Decimal("4161537.00")]])
    ])
    xml = zipfile.ZipFile(io.BytesIO(data)).read("xl/worksheets/sheet1.xml").decode()
    root = ElementTree.fromstring(xml)
    cells = root.findall(f".//{NS}row[@r='2']/{NS}c")
    assert all(c.get("t") != "inlineStr" for c in cells)
    assert cells[0].find(f"{NS}v").text == "46293"          # Excel serial for 2026-09-28
    assert cells[1].find(f"{NS}v").text == "4161537.00"


def test_strings_are_escaped():
    data = build_workbook([Sheet("S", ["A"], [["Ben & Co <ltd>"]])])
    xml = zipfile.ZipFile(io.BytesIO(data)).read("xl/worksheets/sheet1.xml").decode()
    assert "Ben &amp; Co &lt;ltd&gt;" in xml


def test_sheet_names_are_truncated_to_excels_limit():
    data = build_workbook([Sheet("x" * 40, ["A"], [["y"]])])
    xml = zipfile.ZipFile(io.BytesIO(data)).read("xl/workbook.xml").decode()
    assert 'name="' + "x" * 31 + '"' in xml


def test_export_has_a_sheet_per_grouping(sample):
    sheets = sheets_for(sample, analyse(sample), reconcile(sample))
    names = [s.name for s in sheets]
    assert names[0] == "Summary"
    assert "Transactions" in names
    for dimension in GROUPINGS:
        assert f"By {dimension}" in names


def test_export_transactions_sheet_has_every_row(sample):
    sheets = {s.name: s for s in sheets_for(sample, analyse(sample), reconcile(sample))}
    assert len(sheets["Transactions"].rows) == len(sample.transactions)


def test_summary_records_whether_it_reconciled(sample):
    sheets = {s.name: s for s in sheets_for(sample, analyse(sample), reconcile(sample))}
    measures = dict(row[:2] for row in sheets["Summary"].rows)
    assert measures["Reconciled"] == "yes"


# --- dashboard ---------------------------------------------------------

def test_dashboard_embeds_the_workbook_when_given_one(sample):
    page = render(analyse(sample), reconcile(sample), build_workbook([Sheet("S", ["A"], [["x"]])]))
    assert 'download="royal-bliss-cash.xlsx"' in page
    assert "base64," in page


def test_dashboard_has_no_download_without_a_workbook(sample):
    page = render(analyse(sample), reconcile(sample))
    assert "download=" not in page


def test_dashboard_renders_a_panel_per_dimension(sample):
    page = render(analyse(sample), reconcile(sample))
    for dimension in GROUPINGS:
        assert f'data-panel="{dimension}"' in page
        assert f'data-group="{dimension}"' in page


def test_only_the_first_panel_is_visible_at_rest(sample):
    """The page must read correctly before any script runs."""
    page = render(analyse(sample), reconcile(sample))
    assert page.count('class="panel" data-panel=') == len(GROUPINGS)
    assert page.count('" hidden>') == len(GROUPINGS) - 1


# --- CLI guards --------------------------------------------------------

def _scratch_ledger(tmp_path: Path) -> Path:
    for name in ("transactions", "statements"):
        (tmp_path / f"{name}.csv").write_text(
            (DATA / f"{name}.sample.csv").read_text(encoding="utf-8"), encoding="utf-8"
        )
    return tmp_path


def test_manual_override_needs_no_rules_file(tmp_path, capsys):
    """A one-off correction is exactly the case no rule should encode, so
    requiring a rules file for it would be backwards."""
    from finance.cli import main

    data_dir = _scratch_ledger(tmp_path)
    assert main(["--data-dir", str(data_dir), "classify", "--row", "9",
                 "--counterparty", "Supplier Ltd", "--apply"]) == 0
    assert load_transactions(data_dir / "transactions.csv")[7].counterparty == "Supplier Ltd"


def test_manual_override_cannot_contradict_the_bank(tmp_path):
    """Row 9 is a payment. Letting it be marked a receipt would write a ledger
    that refuses to load next time."""
    from finance.cli import main

    data_dir = _scratch_ledger(tmp_path)
    before = (data_dir / "transactions.csv").read_text(encoding="utf-8")
    assert main(["--data-dir", str(data_dir), "classify", "--row", "9",
                 "--category", "cash_in", "--apply"]) == 2
    assert (data_dir / "transactions.csv").read_text(encoding="utf-8") == before


def test_classify_writes_nothing_without_apply(tmp_path):
    from finance.cli import main

    data_dir = _scratch_ledger(tmp_path)
    before = (data_dir / "transactions.csv").read_text(encoding="utf-8")
    assert main(["--data-dir", str(data_dir), "classify", "--row", "9",
                 "--counterparty", "Supplier Ltd"]) == 0
    assert (data_dir / "transactions.csv").read_text(encoding="utf-8") == before
