---
name: uiux-expert
description: Design the interfaces Royal Bliss people actually use — the finance dashboard, its charts and tables, and the public site's pages — covering layout, information hierarchy, money formatting, chart choice, responsive behaviour and accessibility. Use this whenever the user asks to build, lay out, restyle or "make nicer" any screen, dashboard, report, chart or page, when they say a view is hard to read or cluttered, or before writing markup for anything a person will look at.
---

# UI/UX — Royal Bliss

Two audiences, two different jobs:

- **The public site** (`royalbliss/templates/`) persuades. It is read once, by a
  stranger, often on a phone.
- **The finance dashboard** (`finance/report.py`) informs a decision. It is read
  repeatedly, by two or three people who already know the business and want the
  number fast.

Designing the second like the first is the usual failure: hero imagery and
generous whitespace where a director wants the closing balance in the first
screenful.

## Charts: load the `dataviz` skill first

Before writing any chart code, read the `dataviz` skill and follow its
procedure. It is not optional polish — it is how the chart ends up correct
rather than merely colourful. The points that bite hardest here:

- **Pick the form from the data's job**, then colour last.
- **Never a dual-axis chart.** Balance over time and monthly flows are two
  different scales: two charts, not two y-axes.
- **Run the palette validator** rather than reasoning about whether colours are
  distinguishable.
- Cash in versus cash out is **polarity** — a diverging pair with a neutral
  midpoint, not two arbitrary categorical hues.

## Money on screen

Financial readers scan columns of digits; the formatting is load-bearing.

- **Right-align all amounts** and use tabular/monospaced figures so digits line
  up vertically. Ragged decimal points make comparison impossible.
- **Thousands separators, two decimals, always.** `1,280,852.12`, never
  `1280852.1`.
- **Name the currency once** per table or tile (`LKR`), not on every row.
- **Abbreviate only in prose and headline tiles** (LKR 3.14M) — never in a
  table someone might reconcile against a bank statement.
- **Direction by sign and label, not by colour alone.** Red/green is invisible
  to a large minority of readers; pair it with a `+`/`−`, or an "in"/"out"
  label.

## Hierarchy on the dashboard

Order by the question each element answers:

1. **Is the ledger trustworthy?** Reconciliation status goes at the very top.
   A dashboard that silently renders unreconciled data is worse than no
   dashboard — the reader has no way to know the numbers are provisional.
2. **Where do we stand?** Closing balance, net movement, trough.
3. **What happened?** Balance over time, monthly in/out.
4. **Who and what?** Counterparty and category breakdowns.
5. **What needs chasing?** Unpresented cheques, flagged rows, gaps.

Anything a reader must act on belongs above the fold; anything they only
occasionally audit can sit below it.

## Making state visible

- An empty table says **why** it is empty ("no unpresented cheques") rather
  than rendering an empty box.
- A flagged or uncertain value is marked in the row, not footnoted at the
  bottom where it will be missed.
- A number that is a lower bound says so next to itself.

## Accessibility — the parts that are actually load-bearing

- Contrast of at least 4.5:1 for body text, 3:1 for large text and meaningful
  graphics. Check it; do not estimate it.
- Every control reachable and operable by keyboard, with a visible focus ring.
- Real semantics: `<table>` for tabular data with `<th scope>`, headings in
  order, one `<h1>`.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Charts carry a text alternative — a caption stating the takeaway, or an
  adjacent table with the same numbers.

## Responsive

The public site must work from ~360px up, with no horizontal page scroll; only
tables, wide charts and code blocks may scroll, each inside its own container.
The dashboard is desktop-first because it is read at a desk, but it should
still degrade to a single column rather than breaking.

## Before you call a screen done

Look at it rendered, at both widths, in both colour schemes. Then check: can a
reader find the one number they came for in under five seconds; is every
amount aligned and formatted identically; does any colour carry meaning on its
own; does the page scroll sideways; and does an empty or error state look
deliberate rather than broken.
