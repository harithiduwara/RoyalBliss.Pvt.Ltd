"""Render the cash dashboard as a single self-contained HTML file.

No chart library and no network calls: the output is one file that opens from
disk on any machine, which matters because it is never deployed anywhere.

Colour follows the `dataviz` skill. Cash in versus cash out is *polarity*, so
it uses the validated diverging pair (blue/red) rather than two arbitrary
hues; every chart is backed by a table with the same numbers, so identity is
never carried by colour alone.
"""

from __future__ import annotations

import base64
import html
from datetime import date, datetime
from decimal import Decimal

from .analyse import GROUPINGS, Analysis, Bucket
from .money import ZERO, fmt, fmt_short
from .reconcile import ReconciliationReport

# Validated with scripts/validate_palette.js — all six checks pass in both
# modes against the surfaces below. Do not hand-edit these without re-running it.
IN_LIGHT, OUT_LIGHT = "#2a78d6", "#e34948"
IN_DARK, OUT_DARK = "#3987e5", "#e66767"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------- charts


def _line_chart(series: list[tuple[date, Decimal]], *, width: int = 880, height: int = 260) -> str:
    """Balance over time. One series, so no legend — the heading names it."""
    if len(series) < 2:
        return '<p class="empty">Not enough rows yet to plot a balance line.</p>'

    pad_l, pad_r, pad_t, pad_b = 76, 16, 16, 34
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    values = [float(v) for _, v in series]
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1
    # Always include zero so a near-empty account reads as near-empty.
    lo = min(lo, 0.0)
    span = hi - lo

    first, last = series[0][0], series[-1][0]
    total_days = max((last - first).days, 1)

    def x(day: date) -> float:
        return pad_l + plot_w * ((day - first).days / total_days)

    def y(value: float) -> float:
        return pad_t + plot_h * (1 - (value - lo) / span)

    points = " ".join(f"{x(d):.1f},{y(float(v)):.1f}" for d, v in series)
    area = f"{pad_l},{y(0):.1f} " + points + f" {x(last):.1f},{y(0):.1f}"

    # Four gridlines with labelled values; recessive, behind the data.
    grid = []
    for i in range(5):
        value = lo + span * i / 4
        gy = y(value)
        grid.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" class="grid"/>'
            f'<text x="{pad_l - 8}" y="{gy + 4:.1f}" class="tick tick--y">{esc(fmt_short(Decimal(str(value))))}</text>'
        )

    ticks = []
    seen = set()
    for day, _ in series:
        key = (day.year, day.month)
        if key in seen:
            continue
        seen.add(key)
        ticks.append(
            f'<text x="{x(day):.1f}" y="{height - 10}" class="tick tick--x">{day.strftime("%b")}</text>'
        )

    dots = "".join(
        f'<circle cx="{x(d):.1f}" cy="{y(float(v)):.1f}" r="4" class="dot">'
        f"<title>{esc(d)} — LKR {esc(fmt(v))}</title></circle>"
        for d, v in series
    )

    return f"""<svg viewBox="0 0 {width} {height}" class="chart" role="img"
     aria-label="Account balance over time, from {esc(first)} to {esc(last)}">
  {''.join(grid)}
  <polygon points="{area}" class="area"/>
  <polyline points="{points}" class="line"/>
  {dots}
  {''.join(ticks)}
</svg>"""


def _grouped_bars(buckets: list[Bucket], *, width: int = 880, height: int = 280) -> str:
    """Money in and money out per month, side by side on one shared axis.

    Never two y-axes: both series are LKR, so they belong on the same scale,
    and that is the whole point of the comparison.
    """
    if not buckets:
        return '<p class="empty">No monthly activity to show.</p>'

    pad_l, pad_r, pad_t, pad_b = 76, 16, 16, 44
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    peak = max([float(max(b.inflow, b.outflow)) for b in buckets] + [1.0])
    slot = plot_w / len(buckets)
    bar_w = min(38.0, slot / 2.6)
    gap = 2  # the 2px surface gap between adjacent fills

    def bar(value: Decimal, cx: float, klass: str, label: str, month: str) -> str:
        v = float(value)
        h = (v / peak) * plot_h
        if h < 0.5:
            return ""
        y = pad_t + plot_h - h
        return (
            f'<rect x="{cx:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'rx="4" class="{klass}"><title>{esc(month)} {label}: LKR {esc(fmt(value))}</title></rect>'
        )

    grid = []
    for i in range(5):
        value = peak * i / 4
        gy = pad_t + plot_h * (1 - i / 4)
        grid.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" class="grid"/>'
            f'<text x="{pad_l - 8}" y="{gy + 4:.1f}" class="tick tick--y">{esc(fmt_short(Decimal(str(value))))}</text>'
        )

    bars, labels = [], []
    for index, bucket in enumerate(buckets):
        centre = pad_l + slot * (index + 0.5)
        month = datetime.strptime(bucket.key, "%Y-%m").strftime("%b %Y")
        bars.append(bar(bucket.inflow, centre - bar_w - gap / 2, "bar bar--in", "in", month))
        bars.append(bar(bucket.outflow, centre + gap / 2, "bar bar--out", "out", month))
        labels.append(
            f'<text x="{centre:.1f}" y="{height - 24}" class="tick tick--x">{esc(month.split()[0])}</text>'
        )

    baseline_y = pad_t + plot_h
    return f"""<svg viewBox="0 0 {width} {height}" class="chart" role="img"
     aria-label="Money in and money out for each month, in LKR">
  {''.join(grid)}
  <line x1="{pad_l}" y1="{baseline_y}" x2="{width - pad_r}" y2="{baseline_y}" class="baseline"/>
  {''.join(bars)}
  {''.join(labels)}
</svg>"""


def _ranked_bars(buckets: list[Bucket], *, width: int = 880, row_h: int = 34) -> str:
    """Funding by counterparty: one measure across named entities."""
    if not buckets:
        return '<p class="empty">No identified counterparties yet.</p>'

    rows = buckets[:8]
    height = row_h * len(rows) + 10
    label_w, value_w = 150, 130
    track = width - label_w - value_w
    peak = max([float(b.inflow + b.outflow) for b in rows] + [1.0])

    out = []
    for index, bucket in enumerate(rows):
        y = index * row_h + 6
        total = bucket.inflow + bucket.outflow
        bar_w = max((float(total) / peak) * track, 2.0)
        out.append(
            f'<text x="0" y="{y + 18}" class="rank-label">{esc(bucket.key)}</text>'
            f'<rect x="{label_w}" y="{y + 5}" width="{bar_w:.1f}" height="18" rx="4" class="bar bar--in">'
            f"<title>{esc(bucket.key)}: LKR {esc(fmt(total))} across {bucket.count} transaction(s)</title></rect>"
            f'<text x="{width}" y="{y + 18}" class="rank-value">{esc(fmt(total))}</text>'
        )

    return f"""<svg viewBox="0 0 {width} {height}" class="chart" role="img"
     aria-label="Total contributed by each counterparty, in LKR">{''.join(out)}</svg>"""


# ---------------------------------------------------------------- blocks


DIMENSION_LABELS = {
    "counterparty": "Counterparty",
    "category": "Category",
    "month": "Month",
    "week": "Week",
    "branch": "Branch",
    "instrument": "Instrument",
    "direction": "In / out",
}

DIMENSION_NOTES = {
    "counterparty": "Named people and entities only. These are contributions and "
                    "payments, not customer revenue.",
    "category": "What kind of movement it was, on the cash side.",
    "month": "Calendar months across the whole period.",
    "week": "ISO weeks — useful for spotting the rhythm of injections.",
    "branch": "Which Sampath branch or channel the movement went through.",
    "instrument": "Transfer, cheque, counter cash, deposit.",
    "direction": "The simplest cut: everything in against everything out.",
}


def _grouping_block(analysis: Analysis) -> str:
    """Every breakdown rendered up front, with buttons to switch between them.

    Each panel is real HTML in the page rather than something JavaScript builds
    on demand, so the page is complete and printable at rest, and still works
    if the script does not run — the first panel is simply visible.
    """
    buttons, panels = [], []
    for index, dimension in enumerate(GROUPINGS):
        buckets = analysis.groups.get(dimension, [])
        if not buckets:
            continue
        active = "is-active" if index == 0 else ""
        buttons.append(
            f'<button type="button" class="switch {active}" data-group="{dimension}" '
            f'aria-pressed="{"true" if index == 0 else "false"}">'
            f"{esc(DIMENSION_LABELS[dimension])}</button>"
        )
        panels.append(
            f'<div class="panel" data-panel="{dimension}"{"" if index == 0 else " hidden"}>'
            f'<p class="note">{esc(DIMENSION_NOTES[dimension])}</p>'
            f"{_ranked_bars(buckets)}{_bucket_table(buckets, DIMENSION_LABELS[dimension])}"
            "</div>"
        )

    if not panels:
        return '<p class="empty">No transactions to group.</p>'

    return (
        '<div class="switcher" role="group" aria-label="Group the breakdown by">'
        + "".join(buttons)
        + "</div>"
        + "".join(panels)
    )


def _download_block(workbook: bytes | None) -> str:
    if not workbook:
        return ""
    encoded = base64.b64encode(workbook).decode("ascii")
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    size = f"{len(workbook) / 1024:.0f} KB"
    return (
        '<a class="download" download="royal-bliss-cash.xlsx" '
        f'href="data:{mime};base64,{encoded}">'
        '<span aria-hidden="true">↓</span> Download Excel workbook'
        f'<span class="download__size">{size}</span></a>'
    )


def _unclassified_block(analysis: Analysis) -> str:
    if not analysis.unclassified:
        return ""
    rows = "".join(
        f"<tr><td class='mono'>{esc(t.date)}</td><td>{esc(t.particulars)}</td>"
        f"<td class='num'>{esc(fmt(t.debit or t.credit))}</td></tr>"
        for t in analysis.unclassified[:20]
    )
    return f"""<section class="card">
  <h2>Unclassified</h2>
  <p class="note">{len(analysis.unclassified)} row(s) have no category yet, so they
     are missing from the category breakdown. Run
     <span class="mono">classify</span> to apply the rules, or set them by hand
     in the ledger.</p>
  <div class="scroll"><table>
  <thead><tr><th scope="col">Date</th><th scope="col">Particulars</th>
  <th scope="col" class="num">Amount (LKR)</th></tr></thead>
  <tbody>{rows}</tbody></table></div>
</section>"""


def _status_block(report: ReconciliationReport) -> str:
    """Trust first: a reader must know whether these numbers tie to the bank."""
    if report.ok:
        return f"""<section class="status status--ok">
  <p class="status__head"><span class="status__icon" aria-hidden="true">✓</span>
     <strong>Reconciled</strong> — agrees with the bank</p>
  <p class="status__body">{esc(report.summary)}</p>
</section>"""

    items = "".join(
        f"<li><strong>{esc(item.check)}</strong> — {esc(item.where)}<br>"
        f"{esc(item.message)}<br><span class='mono'>difference: LKR {esc(fmt(item.difference))}</span></li>"
        for item in report.discrepancies
    )
    return f"""<section class="status status--bad">
  <p class="status__head"><span class="status__icon" aria-hidden="true">!</span>
     <strong>Not reconciled</strong> — every figure below is provisional</p>
  <ul class="status__list">{items}</ul>
</section>"""


def _tiles(analysis: Analysis) -> str:
    cover = analysis.days_of_cover
    if cover is None:
        cover_text = "n/a"
    elif cover < 1:
        # "1 days" from rounding 0.95 up reads as a day of comfort there isn't.
        cover_text = "under a day"
    else:
        cover_text = f"{cover:.0f} day" + ("s" if cover >= Decimal("1.5") else "")
    tiles = [
        ("Closing balance", fmt_short(analysis.closing_balance), f"LKR {fmt(analysis.closing_balance)}"),
        ("Money in", fmt_short(analysis.total_in), f"LKR {fmt(analysis.total_in)}"),
        ("Money out", fmt_short(analysis.total_out), f"LKR {fmt(analysis.total_out)}"),
        ("Net movement", fmt_short(analysis.net_movement), f"LKR {fmt(analysis.net_movement)}"),
        ("Lowest balance", fmt_short(analysis.trough),
         f"LKR {fmt(analysis.trough)} on {analysis.trough_date}" if analysis.trough_date else "—"),
        ("Cover at current burn", cover_text, f"burn LKR {fmt(analysis.burn_per_month)}/month"),
    ]
    cells = "".join(
        f'<div class="tile"><p class="tile__label">{esc(label)}</p>'
        f'<p class="tile__value">{esc(value)}</p>'
        f'<p class="tile__sub">{esc(sub)}</p></div>'
        for label, value, sub in tiles
    )
    return f'<section class="tiles">{cells}</section>'


def _bucket_table(buckets: list[Bucket], first_col: str) -> str:
    if not buckets:
        return '<p class="empty">Nothing to show.</p>'
    rows = "".join(
        f"<tr><th scope='row'>{esc(b.key)}</th>"
        f"<td class='num'>{esc(fmt(b.inflow)) if b.inflow else '—'}</td>"
        f"<td class='num'>{esc(fmt(b.outflow)) if b.outflow else '—'}</td>"
        f"<td class='num'>{esc(fmt(b.net))}</td>"
        f"<td class='num num--count'>{b.count}</td></tr>"
        for b in buckets
    )
    return f"""<div class="scroll"><table>
<thead><tr><th scope="col">{esc(first_col)}</th><th scope="col" class="num">In</th>
<th scope="col" class="num">Out</th><th scope="col" class="num">Net</th>
<th scope="col" class="num">Rows</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


def _movements_table(transactions, column: str) -> str:
    if not transactions:
        return '<p class="empty">Nothing to show.</p>'
    rows = "".join(
        f"<tr><td class='mono'>{esc(t.date)}</td><td>{esc(t.particulars)}</td>"
        f"<td>{esc(t.counterparty or t.branch)}</td><td>{esc(t.label)}</td>"
        f"<td class='num'>{esc(fmt(t.debit or t.credit))}</td></tr>"
        for t in transactions
    )
    return f"""<div class="scroll"><table>
<thead><tr><th scope="col">Date</th><th scope="col">Particulars</th>
<th scope="col">Who / where</th><th scope="col">Type</th>
<th scope="col" class="num">{esc(column)}</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


def _cheque_block(analysis: Analysis) -> str:
    if not analysis.cheques:
        return '<p class="empty">No own cheques recorded yet.</p>'
    missing = [c for c in analysis.cheques if not c.presented]
    rows = "".join(
        f"<tr class='{'row--flag' if not c.presented else ''}'>"
        f"<td class='mono'>{esc(c.reference)}</td>"
        f"<td class='mono'>{esc(c.date) if c.date else '—'}</td>"
        f"<td class='num'>{esc(fmt(c.amount)) if c.presented else 'amount unknown'}</td>"
        f"<td>{'cleared' if c.presented else 'never seen clearing'}</td></tr>"
        for c in analysis.cheques
    )
    note = (
        f"<p class='note'>{len(missing)} cheque number(s) in the sequence have never "
        "appeared on a statement. Each is unpresented, cancelled, or on a statement "
        "we do not hold. Unpresented cheques are a commitment the bank balance does "
        "not show, so treat the closing balance as an upper bound on available funds.</p>"
        if missing
        else "<p class='note'>Every cheque in the sequence has cleared.</p>"
    )
    return f"""{note}<div class="scroll"><table>
<thead><tr><th scope="col">Cheque</th><th scope="col">Date</th>
<th scope="col" class="num">Amount (LKR)</th><th scope="col">Status</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


def _attention_block(analysis: Analysis, report: ReconciliationReport) -> str:
    parts = []
    if report.flagged:
        items = "".join(f"<li>{esc(line)}</li>" for line in report.flagged)
        parts.append(
            "<h3>Rows flagged when the ledger was entered</h3>"
            f"<ul class='plain'>{items}</ul>"
        )
    if analysis.repeated_amounts:
        rows = "".join(
            "<li><span class='mono'>LKR " + esc(fmt(amount)) + "</span> appears "
            f"{len(txs)} times — "
            + ", ".join(f"{esc(t.date)} {esc(t.particulars)}" for t in txs)
            + "</li>"
            for amount, txs in analysis.repeated_amounts[:6]
        )
        parts.append(
            "<h3>Identical large amounts</h3>"
            "<p class='note'>Usually a standing commitment paid more than once; "
            "occasionally a duplicate payment or a keying error. Worth a look either way.</p>"
            f"<ul class='plain'>{rows}</ul>"
        )
    if not parts:
        return '<p class="empty">Nothing flagged.</p>'
    return "".join(parts)


# ---------------------------------------------------------------- page


def render(
    analysis: Analysis,
    report: ReconciliationReport,
    workbook: bytes | None = None,
) -> str:
    period = (
        f"{analysis.period_start} to {analysis.period_end}"
        if analysis.period_start
        else "no transactions"
    )
    generated = datetime.now().strftime("%d %b %Y, %H:%M")
    concentration = (
        f"The five largest payments are {analysis.outflow_concentration:.1f}% of all money out, "
        "so the average payment size is not a useful summary."
        if analysis.total_out
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Royal Bliss — cash tracker</title>
<style>
:root {{
  color-scheme: light;
  --plane: #f9f9f7; --surface: #fcfcfb;
  --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,.10);
  --in: {IN_LIGHT}; --out: {OUT_LIGHT};
  --good: #0ca30c; --critical: #d03b3b;
  --good-wash: #eaf6ea; --critical-wash: #fdeded;
  --font: system-ui, -apple-system, "Segoe UI", sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --plane: #0d0d0d; --surface: #1a1a19;
    --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10);
    --in: {IN_DARK}; --out: {OUT_DARK};
    --good-wash: #10240f; --critical-wash: #2a1414;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--plane); color: var(--ink-2);
       font-family: var(--font); font-size: 15px; line-height: 1.55; }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px 64px; }}
h1 {{ font-size: 1.6rem; color: var(--ink); margin: 0 0 .15em; }}
h2 {{ font-size: 1.1rem; color: var(--ink); margin: 0 0 .2em; }}
h3 {{ font-size: .95rem; color: var(--ink); margin: 1.4em 0 .4em; }}
.sub {{ color: var(--muted); font-size: .88rem; margin: 0; }}
section.card {{ background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 22px; margin-top: 20px; }}
.card > p.note {{ color: var(--muted); font-size: .86rem; margin: .2em 0 1em; }}
.status {{ border-radius: 12px; padding: 18px 22px; margin-top: 22px;
  border: 1px solid var(--border); }}
.status--ok {{ background: var(--good-wash); }}
.status--bad {{ background: var(--critical-wash); }}
.status__head {{ margin: 0 0 .3em; color: var(--ink); display: flex;
  align-items: center; gap: .6em; }}
.status__icon {{ display: inline-grid; place-items: center; width: 22px; height: 22px;
  border-radius: 50%; color: #fff; font-size: .8rem; font-weight: 700; }}
.status--ok .status__icon {{ background: var(--good); }}
.status--bad .status__icon {{ background: var(--critical); }}
.status__body, .status__list {{ margin: 0; font-size: .9rem; }}
.status__list {{ padding-left: 1.1em; }}
.status__list li {{ margin-top: .5em; }}
.tiles {{ display: grid; gap: 12px; margin-top: 20px;
  grid-template-columns: repeat(auto-fit, minmax(148px, 1fr)); }}
.tile {{ background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px 18px; }}
.tile__label {{ margin: 0; font-size: .76rem; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted); }}
.tile__value {{ margin: .25em 0 .1em; font-size: 1.7rem; font-weight: 650;
  color: var(--ink); line-height: 1.1; }}
.tile__sub {{ margin: 0; font-size: .8rem; color: var(--muted);
  font-variant-numeric: tabular-nums; }}
.chart {{ width: 100%; height: auto; display: block; margin: 10px 0 4px; overflow: visible; }}
.grid {{ stroke: var(--grid); stroke-width: 1; }}
.baseline {{ stroke: var(--axis); stroke-width: 1; }}
.line {{ fill: none; stroke: var(--in); stroke-width: 2;
  stroke-linejoin: round; stroke-linecap: round; }}
.area {{ fill: var(--in); opacity: .10; }}
.dot {{ fill: var(--in); stroke: var(--surface); stroke-width: 2; }}
.bar--in {{ fill: var(--in); }}
.bar--out {{ fill: var(--out); }}
.tick {{ fill: var(--muted); font-size: 11px; font-family: var(--font);
  font-variant-numeric: tabular-nums; }}
.tick--y {{ text-anchor: end; }}
.tick--x {{ text-anchor: middle; }}
.rank-label {{ fill: var(--ink-2); font-size: 13px; font-family: var(--font); }}
.rank-value {{ fill: var(--ink-2); font-size: 13px; font-family: var(--font);
  text-anchor: end; font-variant-numeric: tabular-nums; }}
.legend {{ display: flex; gap: 18px; margin: 4px 0 0; padding: 0; list-style: none;
  font-size: .85rem; color: var(--ink-2); }}
.legend li {{ display: flex; align-items: center; gap: .5em; }}
.swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
.swatch--in {{ background: var(--in); }}
.swatch--out {{ background: var(--out); }}
.scroll {{ overflow-x: auto; margin-top: 10px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 520px; font-size: .88rem; }}
th, td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--border); }}
thead th {{ font-size: .72rem; letter-spacing: .07em; text-transform: uppercase;
  color: var(--muted); font-weight: 600; }}
tbody th {{ font-weight: 500; color: var(--ink); }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.num--count {{ color: var(--muted); }}
.mono {{ font-variant-numeric: tabular-nums; }}
.row--flag td {{ color: var(--critical); }}
.empty {{ color: var(--muted); font-size: .88rem; font-style: italic; margin: 10px 0 0; }}
ul.plain {{ padding-left: 1.1em; font-size: .88rem; }}
ul.plain li {{ margin-bottom: .45em; }}
footer {{ margin-top: 36px; padding-top: 18px; border-top: 1px solid var(--border);
  color: var(--muted); font-size: .82rem; }}
.switcher {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 14px 0 4px; }}
.switch {{ font: inherit; font-size: .84rem; font-weight: 550; cursor: pointer;
  padding: .45em .9em; border-radius: 999px; color: var(--ink-2);
  background: transparent; border: 1px solid var(--border);
  transition: background-color .15s ease, color .15s ease, border-color .15s ease; }}
.switch:hover {{ border-color: var(--in); color: var(--ink); }}
.switch.is-active {{ background: var(--in); border-color: var(--in); color: #fff; }}
.switch:focus-visible {{ outline: 2px solid var(--in); outline-offset: 2px; }}
.download {{ display: inline-flex; align-items: center; gap: .6em; margin-top: 14px;
  padding: .6em 1.1em; border-radius: 10px; text-decoration: none;
  font-size: .88rem; font-weight: 600; color: #fff; background: var(--in);
  border: 1px solid var(--in); }}
.download:hover {{ filter: brightness(1.08); }}
.download:focus-visible {{ outline: 2px solid var(--ink); outline-offset: 2px; }}
.download__size {{ font-weight: 400; opacity: .75; font-variant-numeric: tabular-nums; }}
@media (max-width: 640px) {{ .wrap {{ padding: 20px 14px 48px; }} }}
@media (prefers-reduced-motion: reduce) {{ .switch {{ transition: none; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Royal Bliss (Pvt) Ltd — cash tracker</h1>
    <p class="sub">Sampath Bank current account · LKR · {esc(period)} ·
       {len(analysis.ledger)} transactions · generated {esc(generated)}</p>
    {_download_block(workbook)}
  </header>

  {_status_block(report)}
  {_tiles(analysis)}

  <section class="card">
    <h2>Balance over time</h2>
    <p class="note">The closing balance alone hides the dips. The line shows how
       close the account came to empty between injections. Several movements on
       one day appear as a vertical step — that is real intraday swing, not a
       drawing artefact.</p>
    {_line_chart(analysis.balance_series)}
  </section>

  <section class="card">
    <h2>Money in and out, by month</h2>
    <p class="note">Both series are LKR on one shared scale — never two axes.</p>
    <ul class="legend">
      <li><span class="swatch swatch--in" aria-hidden="true"></span>Money in</li>
      <li><span class="swatch swatch--out" aria-hidden="true"></span>Money out</li>
    </ul>
    {_grouped_bars(analysis.by_month)}
    {_bucket_table(analysis.by_month, "Month")}
  </section>

  <section class="card">
    <h2>Breakdown</h2>
    <p class="note">Group the same transactions seven different ways. Every cut
       covers the whole period, so the totals agree across all of them.</p>
    {_grouping_block(analysis)}
  </section>

  {_unclassified_block(analysis)}

  <section class="card">
    <h2>Where the money goes</h2>
    <p class="note">{esc(concentration)}</p>
    <h3>Largest payments</h3>
    {_movements_table(analysis.largest_out, "Out (LKR)")}
    <h3>Largest receipts</h3>
    {_movements_table(analysis.largest_in, "In (LKR)")}
  </section>

  <section class="card">
    <h2>Cheque register</h2>
    {_cheque_block(analysis)}
  </section>

  <section class="card">
    <h2>Needs attention</h2>
    {_attention_block(analysis, report)}
  </section>

  <footer>
    <p><strong>Confidential.</strong> This file contains company bank data. It is
       written to a git-ignored directory and must not be committed or published.</p>
    <p>Figures are recomputed from the ledger on every run — nothing here is
       cached or hand-entered. Verify against the original statements before
       relying on them for a filing or a board decision.</p>
  </footer>
</div>
<script>
// Switch which breakdown is on screen. Every panel is already in the page, so
// this only toggles visibility — nothing is fetched, computed or lost, and the
// page still reads correctly with the script disabled.
(function () {{
  var switcher = document.querySelector('.switcher');
  if (!switcher) return;
  switcher.addEventListener('click', function (event) {{
    var button = event.target.closest('.switch');
    if (!button) return;
    var wanted = button.dataset.group;
    switcher.querySelectorAll('.switch').forEach(function (other) {{
      var on = other === button;
      other.classList.toggle('is-active', on);
      other.setAttribute('aria-pressed', String(on));
    }});
    document.querySelectorAll('[data-panel]').forEach(function (panel) {{
      panel.hidden = panel.dataset.panel !== wanted;
    }});
  }});
}})();
</script>
</body>
</html>
"""
