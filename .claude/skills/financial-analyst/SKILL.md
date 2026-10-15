---
name: financial-analyst
description: Analyse cash movement, liquidity, burn and funding mix for Royal Bliss (Pvt) Ltd from the bank ledger in data/. Use this whenever the user asks about cash flow, runway, inflows/outflows, "money in and out", where the money went, who is funding the business, how much is left, monthly trends, a particular counterparty or cheque, or wants numbers interpreted rather than just displayed — including when they only hand over a statement and ask "what does this tell me".
---

# Financial analyst — Royal Bliss cash position

You are reading the bank account of an early-stage food & beverage franchise
operator in Sri Lanka. Everything is in **LKR**. The ledger lives at
`data/transactions.csv` (schema in `finance/ledger.py`) and statement-level
control totals at `data/statements.csv`.

Run `python -m finance.cli analyse` first. It prints the numbers this skill
interprets, and it will not let you analyse a ledger that has not reconciled.

## Reconcile before you interpret

An analysis built on an unreconciled ledger is worse than no analysis, because
it is confidently wrong. The CLI reports three checks: running-balance
continuity, statement control totals, and period-to-period continuity. If any
fails, say so first and quantify the gap — a missing statement page is a
finding, not an obstacle to work around.

Never fill a gap with an estimate. If the ledger cannot explain a movement,
the honest output is "LKR X is unexplained between date A and date B; the
statement covering that date is missing".

## What this business actually looks like

Read the shape before computing ratios, because the ratios mean different
things here than in a trading company:

- **Inflows are overwhelmingly funding, not revenue.** Transfers from named
  individuals (Harith, Vihangawe, Mahinda, Pulith, Dunimal) and cash deposits
  are shareholders capitalising the business, not customers paying for food.
  Never call these "revenue" or compute a margin against them.
- **Outflows are set-up spending** — cheques to suppliers, fit-out, equipment,
  deposits — not cost of sales.
- The account cycles: partners inject, a large cheque clears, the balance
  returns to near zero. A low closing balance is therefore not automatically
  distress, but a **consistently** near-zero trough with large cheques pending
  is the thing to flag.

So the questions worth answering are: who is funding this, in what proportion,
how fast is it being spent, and how long until the next injection is needed.

## Metrics that earn their place

| Metric | How to compute | Why it matters here |
|---|---|---|
| Net movement | credits − debits over the period | Whether the account is accumulating or draining |
| Funding mix by partner | sum of credits grouped by counterparty | Shows who is actually carrying the business, and whether contributions are equal |
| Burn rate | total debits ÷ months elapsed | The run-rate of spending |
| Trough balance | minimum running balance in the period | The real liquidity risk; the closing balance flatters it |
| Days of cover | closing balance ÷ (burn ÷ 30) | Blunt but honest runway signal |
| Cheque concentration | largest N debits as % of total debits | One or two cheques usually dominate; averages mislead |

Compute in `Decimal`, never float — these are money amounts and the ledger
reconciles to the cent.

## Writing the analysis

Lead with the finding, then the number, then the caveat. "Partner funding is
uneven: Harith and Vihangawe have each put in ~4.6M while Dunimal has put in
1.28M" is useful. "Total credits were 23,375,908.71" is not, on its own.

Three habits that make the difference:

- **Quantify every claim.** Attach the figure and the date range to each
  statement so the reader can check it against the ledger.
- **Separate observation from inference.** "Four cheques above 1M cleared in
  August" is observation. "This looks like fit-out completing" is inference —
  label it as such, and say what evidence would confirm it.
- **Name what you cannot see.** This is one bank account. You cannot see other
  accounts, cash held outside the bank, liabilities, or what the cheques were
  for. Say so rather than implying the account is the whole picture.

Round only in prose (LKR 1.28M), never in the underlying computation, and
format with thousands separators and two decimals in tables.

## Questions to put back to the business

A good analysis ends with the questions that would unlock the next one:
what are the large recurring cheques paying for, are partner contributions
meant to be equal, is there a second account, and what does the forward
commitment pipeline look like. Ask them rather than guessing.
