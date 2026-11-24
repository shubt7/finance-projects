"""Merger analysis: EPS accretion / dilution and breakeven synergies.

Model
-----
Consideration = stock + cash. Stock issued at the acquirer's share price creates new
shares. Cash consideration is funded with new debt at a pre-tax rate. Pro forma net
income = acquirer NI + target NI + after-tax synergies - after-tax interest.
Accretion = pro forma EPS / standalone EPS - 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MergerInputs:
    acquirer_price: float          # per share
    acquirer_shares: float         # millions
    acquirer_net_income: float     # millions
    target_net_income: float       # millions
    purchase_equity_value: float   # millions
    stock_pct: float               # share of consideration paid in stock, 0..1
    debt_rate: float               # pre-tax cost of new debt used for cash consideration
    synergies_pre_tax: float       # run-rate, millions
    tax_rate: float

    def __post_init__(self):
        if not 0 <= self.stock_pct <= 1:
            raise ValueError("stock_pct must be between 0 and 1")
        if self.acquirer_shares <= 0 or self.acquirer_price <= 0:
            raise ValueError("acquirer price and shares must be positive")
        if self.purchase_equity_value < 0:
            raise ValueError("purchase_equity_value cannot be negative")


@dataclass(frozen=True)
class MergerResult:
    standalone_eps: float
    pro_forma_eps: float
    accretion_pct: float
    new_shares: float
    new_debt: float
    after_tax_interest: float
    pro_forma_net_income: float
    breakeven_synergies_pre_tax: float


def analyse(inp: MergerInputs) -> MergerResult:
    stock_consideration = inp.stock_pct * inp.purchase_equity_value
    cash_consideration = (1 - inp.stock_pct) * inp.purchase_equity_value

    new_shares = stock_consideration / inp.acquirer_price
    new_debt = cash_consideration
    after_tax_interest = new_debt * inp.debt_rate * (1 - inp.tax_rate)

    standalone_eps = inp.acquirer_net_income / inp.acquirer_shares
    pf_ni = (
        inp.acquirer_net_income
        + inp.target_net_income
        + inp.synergies_pre_tax * (1 - inp.tax_rate)
        - after_tax_interest
    )
    pf_shares = inp.acquirer_shares + new_shares
    pro_forma_eps = pf_ni / pf_shares
    accretion = pro_forma_eps / standalone_eps - 1

    # Synergies (pre-tax) that make pro forma EPS exactly equal to standalone EPS.
    ni_needed = standalone_eps * pf_shares
    ni_before_synergies = inp.acquirer_net_income + inp.target_net_income - after_tax_interest
    breakeven = max(0.0, (ni_needed - ni_before_synergies) / (1 - inp.tax_rate))

    return MergerResult(
        standalone_eps=standalone_eps,
        pro_forma_eps=pro_forma_eps,
        accretion_pct=accretion,
        new_shares=new_shares,
        new_debt=new_debt,
        after_tax_interest=after_tax_interest,
        pro_forma_net_income=pf_ni,
        breakeven_synergies_pre_tax=breakeven,
    )


def accretion_by_synergies(inp: MergerInputs, synergy_levels) -> np.ndarray:
    """Accretion / dilution for each synergy level, in the same order as the input."""
    out = []
    for s in synergy_levels:
        params = dict(inp.__dict__)
        params["synergies_pre_tax"] = float(s)
        out.append(analyse(MergerInputs(**params)).accretion_pct)
    return np.array(out)
