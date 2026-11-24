# ib-deal-suite

A deal toolkit for investment banking, by **Shubham**. It covers the three analyses most deal work starts with, and gives each a client view and a banker view.

- **LBO returns:** sources & uses, debt paydown with a cash sweep, sponsor IRR and money multiple, and an entry × exit IRR grid.
- **Merger analysis:** EPS accretion or dilution for stock, cash, or mixed consideration, plus the break-even synergies needed to hold EPS flat.
- **Precedent transactions:** multiple statistics and the implied enterprise value range.
- **Outputs:** a tabbed HTML dashboard (Client view and Banker view), and an Excel workbook with one sheet per analysis.

> All company data in this repo is **hypothetical**. The outputs are illustrative and are not investment advice, a fairness opinion, or a recommendation to buy or sell any security. Verify every input against filings and market data before use.

It pairs with [ib-valuation-toolkit](https://github.com/shubt7/ib-valuation-toolkit), which covers DCF and trading comps.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q                                          # 12 tests
PYTHONPATH=src python scripts/make_deal_report.py  # writes docs/ and the Excel workbook
```

Requires Python 3.10+, NumPy and openpyxl.

## What's inside

| Module | Purpose |
|---|---|
| `dealsuite/lbo.py` | Sources & uses, debt schedule with cash sweep, IRR/MOIC, returns sensitivity |
| `dealsuite/merger.py` | Pro forma EPS, accretion/dilution, break-even synergies, synergy sensitivity |
| `dealsuite/precedents.py` | Multiple statistics and implied enterprise value |
| `dealsuite/excel.py` | Excel export: Summary, LBO, Returns sensitivity, Merger, Precedents |
| `dealsuite/report.py` | Self-contained HTML dashboard with Client and Banker tabs |

## Method

**LBO**
- Annual periods, end-of-year cash flows, no interim dividends.
- Interest is charged on the opening debt balance, so there is no circularity.
- All free cash flow sweeps to debt. Once the debt is repaid, the surplus builds as cash.
- Taxes are floored at zero, with no loss carry-forward.
- Sponsor IRR = MOIC^(1/years) − 1, which is exact because there are no interim cash flows.

**Merger**
- Stock consideration issues new shares at the acquirer's share price.
- Cash consideration is funded with new debt at a pre-tax rate.
- Pro forma NI = acquirer NI + target NI + after-tax synergies − after-tax interest.
- Break-even synergies solve for the pre-tax synergy level at which pro forma EPS equals standalone EPS.

**Precedents**
- Enterprise value uses the 25th percentile, median, and 75th percentile of transaction multiples, applied to the chosen metric.

## Excel workbook

The workbook holds values, not formulas, so it matches the Python model exactly and opens the same everywhere. To change assumptions, edit the inputs in `scripts/make_deal_report.py` and regenerate.

## Replacing the sample data

Edit `lbo_inp`, `merger_inp`, `precedent_multiples`, and `COMPANY` in `scripts/make_deal_report.py`.

## License

MIT. © Shubham
