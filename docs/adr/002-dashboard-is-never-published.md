# ADR 002 — The finance dashboard is never published

Status: accepted · Date: 2026-10-15

## Context
This repository is public and already publishes HTML to GitHub Pages via
`freeze.py`. The cash tracker also renders HTML. Connecting the two would be
easy and would expose the company's bank account number, balances, transaction
history and counterparty names to anyone on the internet.

## Decision
- The tracker is a separate package (`finance/`) with its own entry point. It
  is **not** registered on the Flask app, so the freezer cannot reach it.
- Its output goes to `build-finance/`, which is git-ignored.
- `data/transactions.csv` and `data/statements.csv` are git-ignored. A
  synthetic `*.sample.csv` pair is committed so a fresh clone still runs and
  the tests have fixed data.

## Consequences
Viewing the dashboard requires running `python -m finance.cli report` locally.
That is the cost, and it is worth paying. A test asserts the frozen site
contains no ledger data.

Revisit if: the repository becomes private **and** access control is still
wanted for the dashboard.
