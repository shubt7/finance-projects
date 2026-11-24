"""Self-contained HTML dashboard: a Client view and a Banker view on one page, with tabs.

Plain inline SVG and CSS, no external assets, so it opens anywhere, including a file on disk.
"""

from __future__ import annotations

import html

import numpy as np

from .lbo import LBOInputs, LBOResult, returns_sensitivity
from .merger import MergerInputs, MergerResult
from .precedents import MultipleStats

CSS = """
:root{--bg:#fff;--fg:#1d1d1f;--muted:#6e6e73;--card:#f5f5f7;--grid:#d9d9de;--accent:#0b3d91;--pos:#1a7f37;--neg:#c62828}
@media (prefers-color-scheme: dark){:root{--bg:#111;--fg:#f2f2f2;--muted:#9a9aa0;--card:#1c1c1e;--grid:#333;--accent:#7fb2ff;--pos:#4cc76b;--neg:#ff7b7b}}
body{font:15px/1.55 system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:32px}
main{max-width:1080px;margin:0 auto}
h1{font-size:28px;margin:0 0 4px}h2{font-size:18px;margin:26px 0 10px;color:var(--accent)}
.sub{color:var(--muted);margin-bottom:18px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:14px 0}
.kpi,.card{background:var(--card);border-radius:12px;padding:16px 18px}
.kpi .v{font-size:24px;font-weight:600}.kpi .l{color:var(--muted);font-size:13px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media (max-width:820px){.grid2{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:7px 9px;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:500}
.note{color:var(--muted);font-size:13px;margin-top:8px}
.chart{width:100%;height:auto}.axis{fill:var(--muted);font-size:12px}.lbl{fill:var(--fg);font-size:13px}
.grid{stroke:var(--grid)}.bar{fill:var(--accent);opacity:.85}.bar.neg{fill:var(--neg)}.bar.pos{fill:var(--pos)}
.tabs{display:flex;gap:8px;margin:6px 0 18px}
.tabs button{font:inherit;padding:8px 16px;border-radius:999px;border:1px solid var(--grid);background:var(--card);color:var(--fg);cursor:pointer}
.tabs button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.view{display:none}.view.on{display:block}
.takeaways li{margin-bottom:8px}
.disclaimer{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--grid);padding-top:12px}
"""


def _money(x: float) -> str:
    return f"${x:,.1f}m"


def _pct(x: float) -> str:
    return "n/a" if not np.isfinite(x) else f"{x:.1%}"


def _heat(v: float, lo: float, hi: float) -> str:
    if not np.isfinite(v):
        return "var(--card)"
    t = 0 if hi == lo else (v - lo) / (hi - lo)
    return f"color-mix(in srgb, #0b3d91 {int(12 + 60 * t)}%, var(--card))"


def bar_chart(labels, values, fmt, width=880, height=280, zero_line=True) -> str:
    """Vertical bars; positive and negative values get different colours."""
    pad_l, pad_r, pad_t, pad_b = 52, 16, 16, 44
    vals = np.asarray(values, dtype=float)
    lo, hi = min(0.0, float(np.nanmin(vals))), max(0.0, float(np.nanmax(vals)))
    span = (hi - lo) or 1.0
    lo_p, hi_p = lo - span * 0.08, hi + span * 0.12

    def py(v):
        return pad_t + (1 - (v - lo_p) / (hi_p - lo_p)) * (height - pad_t - pad_b)

    n = len(vals)
    slot = (width - pad_l - pad_r) / n
    bw = slot * 0.6
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for t in np.linspace(lo_p, hi_p, 5):
        y = py(t)
        parts.append(f'<line x1="{pad_l}" x2="{width-pad_r}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{pad_l-6}" y="{y+4:.1f}" class="axis" text-anchor="end">{fmt(t)}</text>')
    if zero_line:
        y0 = py(0)
        parts.append(f'<line x1="{pad_l}" x2="{width-pad_r}" y1="{y0:.1f}" y2="{y0:.1f}" stroke="var(--muted)"/>')
    for i, (lab, v) in enumerate(zip(labels, vals)):
        x = pad_l + i * slot + (slot - bw) / 2
        y_top, y_bot = (py(v), py(0)) if v >= 0 else (py(0), py(v))
        cls = "bar pos" if v >= 0 else "bar neg"
        parts.append(f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{bw:.1f}" height="{max(y_bot-y_top,1):.1f}" rx="3" class="{cls}"/>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{height-pad_b+16}" class="axis" text-anchor="middle">{html.escape(str(lab))}</text>')
        ly = y_top - 5 if v >= 0 else y_bot + 12
        parts.append(f'<text x="{x+bw/2:.1f}" y="{ly:.1f}" class="lbl" text-anchor="middle">{fmt(v)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def football_range(stats: MultipleStats, metric: float, metric_name: str, width=880) -> str:
    """Horizontal range bars: low–high, interquartile, and median, in $m EV."""
    rows = [
        ("Precedent range (low–high)", stats.low * metric, stats.high * metric),
        ("Interquartile (25th–75th)", stats.p25 * metric, stats.p75 * metric),
    ]
    lo = min(r[1] for r in rows) * 0.9
    hi = max(r[2] for r in rows) * 1.06
    left, right, top, row_h = 250, 24, 14, 50
    height = top + row_h * len(rows) + 60

    def px(v):
        return left + (v - lo) / (hi - lo) * (width - left - right)

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for t in np.linspace(lo, hi, 5):
        x = px(t)
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{height-34}" class="grid"/>')
        parts.append(f'<text x="{x:.1f}" y="{height-22}" class="axis" text-anchor="middle">${t:,.0f}m</text>')
    for i, (lab, a, b) in enumerate(rows):
        y = top + i * row_h
        parts.append(f'<text x="{left-10}" y="{y+row_h/2+4:.1f}" class="lbl" text-anchor="end">{html.escape(lab)}</text>')
        parts.append(f'<rect x="{px(a):.1f}" y="{y+10}" width="{max(px(b)-px(a),2):.1f}" height="{row_h-20}" rx="4" class="bar"/>')
        parts.append(f'<text x="{px(a)-6:.1f}" y="{y+row_h/2+4:.1f}" class="axis" text-anchor="end">${a:,.0f}m</text>')
        parts.append(f'<text x="{px(b)+6:.1f}" y="{y+row_h/2+4:.1f}" class="axis">${b:,.0f}m</text>')
    parts.append(f'<text x="{width/2:.0f}" y="{height-4}" class="axis" text-anchor="middle">Enterprise value at {stats.median:.1f}x median {html.escape(metric_name)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _client_view(company, lbo_inp, lbo, merger, merger_synergies, stats, metric, exit_multiples, entry_multiples, grid) -> str:
    su = lbo.sources_uses
    accretive = merger.accretion_pct >= 0
    takeaways = [
        f"At a {lbo_inp.entry_multiple:.1f}x entry and {lbo_inp.exit_multiple:.1f}x exit, the sponsor's projected return is "
        f"<b>{_pct(lbo.irr)} IRR</b> and <b>{lbo.moic:.2f}x money multiple</b> over {len(lbo.years)} years.",
        f"The deal is funded with <b>{_money(su.debt)} of debt</b> and <b>{_money(su.sponsor_equity)} of equity</b>.",
        f"The merger is <b>{'accretive' if accretive else 'dilutive'} by {_pct(abs(merger.accretion_pct))}</b> to EPS, "
        f"including {_money(merger_synergies)} of pre-tax synergies per year.",
        f"Break-even synergies are about <b>{_money(merger.breakeven_synergies_pre_tax)} pre-tax</b> per year.",
        f"Precedent transactions imply an enterprise value between roughly "
        f"<b>{_money(stats.p25 * metric)} and {_money(stats.p75 * metric)}</b>.",
    ]
    lis = "".join(f"<li>{t}</li>" for t in takeaways)
    return f"""
<div class="kpis">
  <div class="kpi"><div class="v">{_pct(lbo.irr)}</div><div class="l">Sponsor IRR</div></div>
  <div class="kpi"><div class="v">{lbo.moic:.2f}x</div><div class="l">Money multiple (MOIC)</div></div>
  <div class="kpi"><div class="v">{_pct(merger.accretion_pct)}</div><div class="l">EPS accretion / (dilution)</div></div>
  <div class="kpi"><div class="v">{_money(su.purchase_ev)}</div><div class="l">Purchase enterprise value</div></div>
</div>
<h2>Key takeaways</h2>
<div class="card"><ul class="takeaways">{lis}</ul></div>
<h2>Where value comes from</h2>
<div class="card">{football_range(stats, metric, "EBITDA")}
<div class="note">Enterprise value ranges from precedent transaction multiples applied to {company}'s LTM EBITDA.</div></div>
"""


def _banker_view(company, lbo_inp, lbo, merger_inp, merger, stats, metric,
                 exit_multiples, entry_multiples, grid, synergy_levels, accretion_values) -> str:
    su = lbo.sources_uses
    yrs = "".join(f"<th>Y{int(y)}</th>" for y in lbo.years)

    def row(name, arr, fmt=lambda v: f"{v:,.1f}"):
        return f"<tr><td>{name}</td>" + "".join(f"<td>{fmt(v)}</td>" for v in arr) + "</tr>"

    proj = (f"<table><tr><th>$m</th>{yrs}</tr>"
            + row("Revenue", lbo.revenue) + row("EBITDA", lbo.ebitda)
            + row("Interest", lbo.interest) + row("Net income", lbo.net_income)
            + row("Free cash flow", lbo.free_cash_flow)
            + row("Debt (closing)", lbo.debt) + row("Net debt", lbo.net_debt)
            + row("Net debt / EBITDA", lbo.leverage_path, lambda v: f"{v:.1f}x") + "</table>")

    su_tbl = (f"<table><tr><th>Sources &amp; uses</th><th>$m</th></tr>"
              f"<tr><td>Purchase enterprise value</td><td>{su.purchase_ev:,.1f}</td></tr>"
              f"<tr><td>Fees</td><td>{su.fees:,.1f}</td></tr>"
              f"<tr><td><b>Total uses</b></td><td><b>{su.total_uses:,.1f}</b></td></tr>"
              f"<tr><td>New debt</td><td>{su.debt:,.1f}</td></tr>"
              f"<tr><td>Sponsor equity</td><td>{su.sponsor_equity:,.1f} ({su.equity_pct:.0%})</td></tr>"
              f"<tr><td><b>Exit equity value</b></td><td><b>{lbo.exit_equity:,.1f}</b></td></tr></table>")

    lo, hi = float(np.nanmin(grid)), float(np.nanmax(grid))
    head = "".join(f"<th>{x:.1f}x exit</th>" for x in exit_multiples)
    body = []
    for i, em in enumerate(entry_multiples):
        cells = "".join(
            f'<td style="background:{_heat(grid[i, j], lo, hi)}">{_pct(grid[i, j])}</td>'
            for j in range(len(exit_multiples))
        )
        body.append(f"<tr><td>{em:.1f}x entry</td>{cells}</tr>")
    sens = f"<table><tr><th></th>{head}</tr>{''.join(body)}</table>"

    merger_tbl = (f"<table><tr><th>Merger</th><th>Value</th></tr>"
                  f"<tr><td>Standalone EPS</td><td>{merger.standalone_eps:.2f}</td></tr>"
                  f"<tr><td>Pro forma EPS</td><td>{merger.pro_forma_eps:.2f}</td></tr>"
                  f"<tr><td>New shares issued (m)</td><td>{merger.new_shares:,.2f}</td></tr>"
                  f"<tr><td>New debt for cash consideration ($m)</td><td>{merger.new_debt:,.1f}</td></tr>"
                  f"<tr><td>Break-even synergies, pre-tax ($m)</td><td>{merger.breakeven_synergies_pre_tax:,.1f}</td></tr>"
                  f"</table>")

    return f"""
<h2>Projections and debt paydown</h2><div class="card">{proj}</div>
<div class="grid2">
  <div class="card"><h2 style="margin-top:0">Sources &amp; uses and exit</h2>{su_tbl}</div>
  <div class="card"><h2 style="margin-top:0">Merger</h2>{merger_tbl}</div>
</div>
<h2>Sponsor IRR sensitivity</h2>
<div class="card">{sens}<div class="note">Rows: entry multiple. Columns: exit multiple. Darker is higher IRR.</div></div>
<h2>EPS accretion / (dilution) by synergy level</h2>
<div class="card">{bar_chart([f"${s:,.0f}m" for s in synergy_levels], [a*100 for a in accretion_values], lambda v: f"{v:.1f}%")}
<div class="note">Pre-tax synergies, $m. Bars below zero are dilutive.</div></div>
"""


def build_dashboard(company: str, lbo_inp: LBOInputs, lbo: LBOResult, merger_inp: MergerInputs,
                    merger: MergerResult, stats: MultipleStats, metric: float,
                    exit_multiples, entry_multiples, synergy_levels, accretion_values,
                    prepared_by: str = "") -> str:
    grid = returns_sensitivity(lbo_inp, exit_multiples, entry_multiples)
    client = _client_view(company, lbo_inp, lbo, merger, merger_inp.synergies_pre_tax, stats, metric, exit_multiples, entry_multiples, grid)
    banker = _banker_view(company, lbo_inp, lbo, merger_inp, merger, stats, metric,
                          exit_multiples, entry_multiples, grid, synergy_levels, accretion_values)
    by = f" · prepared by {html.escape(prepared_by)}" if prepared_by else ""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(company)} deal dashboard</title>
<style>{CSS}</style></head><body><main>
<h1>{html.escape(company)}: deal dashboard</h1>
<div class="sub">Illustrative analysis on hypothetical inputs{by}</div>
<nav class="tabs"><button class="on" data-v="client">Client view</button><button data-v="banker">Banker view</button></nav>
<section class="view on" id="client">{client}</section>
<section class="view" id="banker">{banker}</section>
<div class="disclaimer">Illustrative analysis on hypothetical inputs. Not investment advice, a fairness opinion, or a recommendation to buy or sell any security. Verify every input before use.</div>
</main><script>
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('on',v.id===b.dataset.v));
}});
</script></body></html>"""
