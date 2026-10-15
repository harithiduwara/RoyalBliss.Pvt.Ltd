# ADR 001 — CSV is the ledger, not a database

Status: accepted · Date: 2026-10-15

## Context
The cash tracker needs somewhere to keep bank transactions. The obvious
alternatives were SQLite and a CSV file.

## Decision
A CSV file at `data/transactions.csv`, loaded fresh on every run.

## Consequences
It is diffable in git, editable in any spreadsheet without this tool, readable
by someone who has never seen the code, and survives the project being
abandoned — which matters more for a few hundred rows of company records than
query performance does. Concurrent writes are unsafe, and there is no indexed
querying; neither is needed by a single bookkeeper working from paper
statements.

Revisit if: more than one person edits the ledger at the same time, or the row
count reaches the hundreds of thousands.
