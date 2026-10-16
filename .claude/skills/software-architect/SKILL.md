---
name: software-architect
description: Make and record structural decisions for the Royal Bliss codebase — how the website, the finance tracker and the dashboard fit together, what may be published versus kept local, dependency and data-store choices, and ADRs. Use this whenever a change spans more than one module, introduces a dependency or service, changes where data lives or how it is deployed, when someone asks "where should this go" or "should we use X", or when a request would quietly undo a constraint the project is built on.
---

# Software architect — Royal Bliss

Two things live in this repository and they must not blur together:

1. **The public website** — a Flask app frozen to static HTML by `freeze.py`
   and deployed to GitHub Pages. Public, marketing, no secrets.
2. **The finance tracker** — a local Python tool over `data/transactions.csv`
   that produces a dashboard. **Company bank data. Never published.**

Most architectural mistakes available here consist of accidentally connecting
those two.

## The constraints you are defending

These were chosen deliberately. Changing one is legitimate; changing one by
accident is not.

- **GitHub Pages hosts static files only.** Anything requiring a server at
  request time cannot be part of the published site. This is why the contact
  form posts to a third-party endpoint rather than a Flask route.
- **The repository is public.** Therefore `data/transactions.csv` is
  git-ignored and the finance dashboard is written to `build-finance/`, which
  is also ignored. Before adding any finance output to a tracked path or to a
  route the freezer can reach, stop: that publishes the company's bank account
  to the internet.
- **The freezer only emits what it can reach.** A finance route registered on
  the Flask app would be crawled and published. Keep the tracker out of the
  Flask app entirely — it is a separate package with its own entry point.
- **Few dependencies.** The site needs Flask and Frozen-Flask; the tracker
  needs only the standard library. This keeps the tool runnable on any machine
  with Python and auditable by someone who did not write it.

## Deciding where something goes

| The change is about… | It belongs in | Published? |
|---|---|---|
| Marketing copy, pages, SEO | `royalbliss/` | Yes |
| Ledger schema, validation, reconciliation | `finance/` | No |
| Analysis and KPIs | `finance/analyse.py` | No |
| Dashboard rendering | `finance/report.py` → `build-finance/` | No |
| Real transactions | `data/transactions.csv` (git-ignored) | No |
| Example data for tests and demos | `data/transactions.sample.csv` | Yes — must be synthetic |

If a change does not fit this table, that is a signal to think rather than to
improvise a new location.

## Money, data and determinism

- **`Decimal` for all amounts, never float.** The ledger reconciles to the
  cent against the bank's printed totals; binary floating point breaks that
  silently and you will not notice until a total is 0.01 out.
- **CSV is the source of truth, deliberately.** It is diffable, auditable,
  editable without the tool, and survives the project being abandoned. A
  database would buy concurrent writes and querying that a single-operator
  ledger of a few hundred rows does not need. Revisit when there are multiple
  concurrent editors or hundreds of thousands of rows — not before.
- **Derived values are never stored.** Everything the dashboard shows is
  recomputed from the ledger on each run, so there is no stale cache to
  reconcile and the output is reproducible from evidence.

## Recording decisions

When a decision closes off an option someone would plausibly reach for, write
it down in `docs/adr/NNN-short-title.md`:

```
# ADR 003 — Keep the finance dashboard out of the published site
Status: accepted · Date: 2026-10-15
Context: The tracker renders HTML, and the site already publishes HTML to Pages.
Decision: Render to build-finance/, git-ignored, never routed through the Flask app.
Consequences: Viewing it requires running the tool locally. Accepted, because
the alternative publishes the company's bank account on a public repository.
Revisit if: the repository becomes private AND access control is still wanted.
```

The "revisit if" line is what stops an ADR becoming dogma.

## Reviewing a proposed change

Ask: does it cross the public/private boundary; does it add a dependency and
is that dependency worth its maintenance; does it store something that could
be derived; does it make the output non-reproducible; and would someone
reading the repo in six months understand why. Any "yes" to the first four is
worth a conversation before code.
