# ADR 003 — Decimal for every amount, never float

Status: accepted · Date: 2026-10-15

## Context
The ledger reconciles to the cent against totals printed on bank statements.
Binary floating point cannot represent 0.10 exactly, so sums drift.

## Decision
Every monetary value is a `decimal.Decimal`, parsed from the CSV as a string.

## Consequences
Equality comparisons against the bank's printed totals are exact, so
reconciliation is a real check rather than an approximate one. Any new code
touching money must not introduce `float()`; a test asserts exactness.
