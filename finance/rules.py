"""Classification rules.

Classifying the same recurring payment by hand every month is how ledgers rot:
it is tedious, so it gets skipped, and then the categories mean nothing. Rules
make it repeatable — write "anything whose particulars contain VSRTFR-Harith is
a transfer in from Harith" once, and every future statement obeys it.

Rules never invent a direction. Whether a row is money in or money out comes
from which column the bank put the amount in, and a rule that disagrees with
that is rejected rather than applied — a rule file should not be able to turn
a payment into a receipt.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from .ledger import CATEGORIES, INFLOW_CATEGORIES, LedgerError, Transaction

RULE_FIELDS = ["match_field", "pattern", "category", "counterparty", "note"]
MATCH_FIELDS = {"particulars", "branch", "instrument", "reference", "counterparty", "any"}


@dataclass(frozen=True)
class Rule:
    match_field: str
    pattern: str
    category: str
    counterparty: str
    note: str
    line: int = 0

    @property
    def is_regex(self) -> bool:
        return self.pattern.startswith("re:")

    def matches(self, tx: Transaction) -> bool:
        if self.match_field == "any":
            haystack = " ".join(
                [tx.particulars, tx.branch, tx.instrument, tx.reference, tx.counterparty]
            )
        else:
            haystack = getattr(tx, self.match_field, "")

        if self.is_regex:
            return bool(re.search(self.pattern[3:], haystack, re.IGNORECASE))
        return self.pattern.casefold() in haystack.casefold()


@dataclass
class Change:
    transaction: Transaction
    rule: Rule
    category: str | None
    counterparty: str | None

    def describe(self) -> str:
        bits = []
        if self.category:
            bits.append(f"category {self.transaction.category} -> {self.category}")
        if self.counterparty:
            previous = self.transaction.counterparty or "(blank)"
            bits.append(f"counterparty {previous} -> {self.counterparty}")
        return "; ".join(bits)


def load_rules(path: Path | str) -> list[Rule]:
    path = Path(path)
    if not path.exists():
        return []

    rules: list[Rule] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [f for f in RULE_FIELDS if f not in (reader.fieldnames or [])]
        if missing:
            raise LedgerError(f"{path}: missing column(s): {', '.join(missing)}")

        for offset, row in enumerate(reader, start=2):
            pattern = (row["pattern"] or "").strip()
            if not pattern:
                continue

            match_field = (row["match_field"] or "any").strip().lower()
            if match_field not in MATCH_FIELDS:
                raise LedgerError(
                    f"{path} line {offset}: unknown match_field {match_field!r}. "
                    f"Expected one of: {', '.join(sorted(MATCH_FIELDS))}"
                )

            category = (row["category"] or "").strip()
            if category and category not in CATEGORIES:
                raise LedgerError(
                    f"{path} line {offset}: unknown category {category!r}. "
                    f"Expected one of: {', '.join(sorted(CATEGORIES))}"
                )

            rule = Rule(
                match_field=match_field,
                pattern=pattern,
                category=category,
                counterparty=(row["counterparty"] or "").strip(),
                note=(row["note"] or "").strip(),
                line=offset,
            )
            if rule.is_regex:
                try:
                    re.compile(rule.pattern[3:])
                except re.error as exc:
                    raise LedgerError(
                        f"{path} line {offset}: bad regular expression — {exc}"
                    ) from exc
            rules.append(rule)
    return rules


def plan(
    transactions: list[Transaction],
    rules: list[Rule],
    *,
    reclassify_all: bool = False,
) -> tuple[list[Change], list[str]]:
    """Work out what the rules would change, without changing anything.

    Returns the changes and any warnings. Nothing is written here: seeing the
    diff before it touches the ledger is the point, because a careless rule can
    silently recategorise months of history.
    """
    changes: list[Change] = []
    warnings: list[str] = []

    for tx in transactions:
        settled = tx.category != "unclassified"
        if settled and not reclassify_all:
            # Still fill in a blank counterparty — that is additive and safe.
            for rule in rules:
                if rule.counterparty and not tx.counterparty and rule.matches(tx):
                    changes.append(Change(tx, rule, None, rule.counterparty))
                    break
            continue

        for rule in rules:  # first match wins, so order is meaningful
            if not rule.matches(tx):
                continue

            category = rule.category or None
            if category and category != "unclassified":
                rule_is_inflow = category in INFLOW_CATEGORIES
                if rule_is_inflow != tx.is_inflow:
                    warnings.append(
                        f"row {tx.row_number} ({tx.date} {tx.particulars}): rule on "
                        f"line {rule.line} wants {category!r}, but the bank recorded "
                        f"this as money {'in' if tx.is_inflow else 'out'}. Skipped — "
                        "fix the rule rather than the statement."
                    )
                    continue

            counterparty = rule.counterparty or None
            if counterparty and counterparty == tx.counterparty:
                counterparty = None
            if category or counterparty:
                changes.append(Change(tx, rule, category, counterparty))
            break

    return changes, warnings


def apply_changes(path: Path | str, changes: list[Change]) -> int:
    """Write the changes back to the ledger CSV, preserving every other column."""
    path = Path(path)
    by_row = {c.transaction.row_number: c for c in changes}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    written = 0
    for offset, row in enumerate(rows, start=2):
        change = by_row.get(offset)
        if not change:
            continue
        if change.category:
            row["category"] = change.category
        if change.counterparty:
            row["counterparty"] = change.counterparty
        written += 1

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return written
