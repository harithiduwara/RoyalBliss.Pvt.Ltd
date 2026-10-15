# Ledger data

| File | Tracked in git? | What it is |
|---|---|---|
| `transactions.sample.csv` | yes | Synthetic example. Safe to publish. Used by the tests. |
| `statements.sample.csv` | yes | Control totals for the sample. |
| `transactions.csv` | **no — git-ignored** | The real bank ledger. |
| `statements.csv` | **no — git-ignored** | Real statement control totals. |

The real files are ignored on purpose: this repository is public, and the
ledger contains the company's account number, balances and counterparty names.
The tools fall back to the sample files when the real ones are absent, so a
fresh clone still runs.

## Columns

| Column | Meaning |
|---|---|
| `date` | Value date as printed, `YYYY-MM-DD` |
| `statement_id` | Which statement the row came from; links to `statements.csv` |
| `branch` | Branch or channel in the PARTICULARS column |
| `particulars` | The description as printed — do not tidy it |
| `counterparty` | Person or entity, where identifiable |
| `instrument` | VSRTFR, CHQ_OUT, CHQ_IN, CACHQ, TRCHQ, CASH, CHARGE, DEPOSIT |
| `reference` | Cheque number. Short numbers are our own cheques; long ones are drawn on another account |
| `debit` | Money out. Blank on a credit row |
| `credit` | Money in. Blank on a debit row |
| `balance` | **The balance the bank printed.** Never a computed figure — this is what reconciliation checks against |
| `category` | Cash-side classification (see `finance/ledger.py`) |
| `needs_review` | `yes` when a value could not be read with confidence |
| `note` | Why it is flagged, or anything a reader needs to know |

Amounts are positive in both columns; direction comes from which column the
amount is in, never from a minus sign.
