"""Build the deal dashboard (HTML) and the Excel workbook for the illustrative deal.

Run:  PYTHONPATH=src python scripts/make_deal_report.py

All figures are hypothetical. Replace the inputs with verified data before use.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from dealsuite import (
    LBOInputs,
    MergerInputs,
    accretion_by_synergies,
    analyse,
    build_dashboard,
    run,
    summarise,
    write_workbook,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
COMPANY = "Target Co (hypothetical)"
PREPARED_BY = "Shubham"

lbo_inp = LBOInputs(
    revenue0=500.0,
    ebitda0=100.0,
    revenue_growth=(0.08, 0.08, 0.07, 0.06, 0.05),
    ebitda_margin=0.20,
    entry_multiple=10.0,
    exit_multiple=10.0,
    leverage=5.0,
    interest_rate=0.08,
    tax_rate=0.25,
    da_pct_revenue=0.03,
    capex_pct_revenue=0.04,
    nwc_pct_revenue=0.10,
    fee_pct=0.02,
)
merger_inp = MergerInputs(
    acquirer_price=50.0,
    acquirer_shares=120.0,
    acquirer_net_income=260.0,
    target_net_income=40.0,
    purchase_equity_value=900.0,
    stock_pct=0.4,
    debt_rate=0.065,
    synergies_pre_tax=15.0,
    tax_rate=0.25,
)
precedent_multiples = np.array([7.8, 8.4, 9.0, 9.6, 10.2, 10.9, 11.5, 12.4])
exit_multiples = [8.0, 9.0, 10.0, 11.0, 12.0]
entry_multiples = [9.0, 10.0, 11.0]
synergy_levels = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]

lbo = run(lbo_inp)
merger = analyse(merger_inp)
stats = summarise(precedent_multiples)
accretion_values = accretion_by_synergies(merger_inp, synergy_levels)

DOCS.mkdir(parents=True, exist_ok=True)
(DOCS / "deal_dashboard.html").write_text(
    build_dashboard(
        COMPANY, lbo_inp, lbo, merger_inp, merger, stats, metric=lbo_inp.ebitda0,
        exit_multiples=exit_multiples, entry_multiples=entry_multiples,
        synergy_levels=synergy_levels, accretion_values=accretion_values,
        prepared_by=PREPARED_BY,
    ),
    encoding="utf-8",
)
write_workbook(
    DOCS / "deal_model.xlsx", COMPANY, lbo_inp, lbo, merger_inp, merger, stats,
    exit_multiples, entry_multiples, synergy_levels, accretion_values,
)

print(f"IRR {lbo.irr:.1%}  MOIC {lbo.moic:.2f}x  accretion {merger.accretion_pct:.1%}  "
      f"breakeven synergies {merger.breakeven_synergies_pre_tax:.1f}")
