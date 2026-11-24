"""Excel export: one workbook with the deal model, sensitivities and precedents.

Values are written as numbers with number formats. Formulas are not used, so the
workbook opens identically everywhere and matches the Python model exactly.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .lbo import LBOInputs, LBOResult, returns_sensitivity
from .merger import MergerInputs, MergerResult
from .precedents import MultipleStats

HEADER_FILL = PatternFill("solid", fgColor="0B3D91")
HEADER_FONT = Font(bold=True, color="FFFFFF")
BOLD = Font(bold=True)


def _header(ws, row: int, values) -> None:
    for col, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=col, value=v)
        c.fill, c.font = HEADER_FILL, HEADER_FONT
        c.alignment = Alignment(horizontal="center")


def _widths(ws, widths) -> None:
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_workbook(
    path: Path,
    company: str,
    lbo_inp: LBOInputs,
    lbo: LBOResult,
    merger_inp: MergerInputs,
    merger: MergerResult,
    precedent_stats: MultipleStats,
    exit_multiples,
    entry_multiples,
    synergy_levels,
    accretion_values,
) -> None:
    wb = Workbook()

    # Summary
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = f"{company}: deal summary"
    ws["A1"].font = Font(bold=True, size=14)
    rows = [
        ("Sponsor IRR", lbo.irr, "0.0%"),
        ("Sponsor MOIC", lbo.moic, '0.00"x"'),
        ("Sponsor equity ($m)", lbo.sources_uses.sponsor_equity, "#,##0.0"),
        ("Opening leverage (x EBITDA)", lbo_inp.leverage, '0.0"x"'),
        ("Standalone EPS", merger.standalone_eps, "0.00"),
        ("Pro forma EPS", merger.pro_forma_eps, "0.00"),
        ("EPS accretion / (dilution)", merger.accretion_pct, "0.0%"),
        ("Breakeven synergies, pre-tax ($m)", merger.breakeven_synergies_pre_tax, "#,##0.0"),
        ("Precedent median multiple", precedent_stats.median, '0.0"x"'),
    ]
    _header(ws, 3, ["Metric", "Value"])
    for r, (label, value, fmt) in enumerate(rows, start=4):
        ws.cell(row=r, column=1, value=label)
        c = ws.cell(row=r, column=2, value=value)
        c.number_format = fmt
    _widths(ws, [38, 16])

    # LBO projections
    ws = wb.create_sheet("LBO")
    years = [f"Y{int(y)}" for y in lbo.years]
    _header(ws, 1, ["$m"] + years)
    series = [
        ("Revenue", lbo.revenue),
        ("EBITDA", lbo.ebitda),
        ("Interest", lbo.interest),
        ("Net income", lbo.net_income),
        ("Free cash flow", lbo.free_cash_flow),
        ("Debt (closing)", lbo.debt),
        ("Cash (closing)", lbo.cash),
        ("Net debt", lbo.net_debt),
        ("Net debt / EBITDA", lbo.leverage_path),
    ]
    for r, (label, arr) in enumerate(series, start=2):
        ws.cell(row=r, column=1, value=label).font = BOLD
        fmt = '0.0"x"' if label.startswith("Net debt /") else "#,##0.0"
        for c, v in enumerate(arr, start=2):
            cell = ws.cell(row=r, column=c, value=float(v))
            cell.number_format = fmt

    su = lbo.sources_uses
    r0 = len(series) + 4
    _header(ws, r0, ["Sources & uses ($m)", "Value"])
    for i, (label, v) in enumerate(
        [
            ("Purchase enterprise value", su.purchase_ev),
            ("Fees", su.fees),
            ("Total uses", su.total_uses),
            ("New debt", su.debt),
            ("Sponsor equity", su.sponsor_equity),
            ("Equity % of uses", su.equity_pct),
        ],
        start=r0 + 1,
    ):
        ws.cell(row=i, column=1, value=label)
        ws.cell(row=i, column=2, value=float(v)).number_format = "0.0%" if "%" in label else "#,##0.0"
    _widths(ws, [30] + [12] * len(years))

    # Returns sensitivity
    ws = wb.create_sheet("Returns sensitivity")
    grid = returns_sensitivity(lbo_inp, exit_multiples, entry_multiples)
    ws["A1"] = "Sponsor IRR: entry multiple (rows) vs exit multiple (columns)"
    ws["A1"].font = BOLD
    _header(ws, 3, ["Entry \\ Exit"] + [f"{x:.1f}x" for x in exit_multiples])
    for i, em in enumerate(entry_multiples):
        ws.cell(row=4 + i, column=1, value=f"{em:.1f}x").font = BOLD
        for j in range(len(exit_multiples)):
            c = ws.cell(row=4 + i, column=2 + j, value=float(grid[i, j]))
            c.number_format = "0.0%"
    _widths(ws, [16] + [12] * len(exit_multiples))

    # Merger
    ws = wb.create_sheet("Merger")
    _header(ws, 1, ["Synergies, pre-tax ($m)", "EPS accretion / (dilution)"])
    for r, (s, a) in enumerate(zip(synergy_levels, accretion_values), start=2):
        ws.cell(row=r, column=1, value=float(s)).number_format = "#,##0.0"
        ws.cell(row=r, column=2, value=float(a)).number_format = "0.0%"
    _widths(ws, [26, 26])

    # Precedents
    ws = wb.create_sheet("Precedents")
    _header(ws, 1, ["Statistic", "EV / EBITDA"])
    stats = [
        ("Count", precedent_stats.count, "0"),
        ("Low", precedent_stats.low, '0.0"x"'),
        ("25th percentile", precedent_stats.p25, '0.0"x"'),
        ("Median", precedent_stats.median, '0.0"x"'),
        ("Mean", precedent_stats.mean, '0.0"x"'),
        ("75th percentile", precedent_stats.p75, '0.0"x"'),
        ("High", precedent_stats.high, '0.0"x"'),
    ]
    for r, (label, v, fmt) in enumerate(stats, start=2):
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=float(v)).number_format = fmt
    _widths(ws, [22, 16])

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
