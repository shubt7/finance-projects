"""Leveraged buyout (LBO) model: sources & uses, debt paydown, sponsor returns.

Conventions
-----------
* Annual periods, end-of-year cash flows, no interim dividends.
* Single debt tranche at a fixed interest rate on the opening balance (no circularity).
* 100% of free cash flow sweeps to debt; any excess after debt is fully repaid builds cash.
* Taxes are floored at zero (no NOL carry-forward) to keep the model transparent.
* Sponsor IRR = MOIC ** (1 / years) - 1, valid because there are no interim cash flows.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LBOInputs:
    revenue0: float
    ebitda0: float
    revenue_growth: tuple[float, ...]
    ebitda_margin: float
    entry_multiple: float          # EV / LTM EBITDA paid at close
    exit_multiple: float           # EV / exit-year EBITDA
    leverage: float                # opening debt / LTM EBITDA
    interest_rate: float
    tax_rate: float
    da_pct_revenue: float
    capex_pct_revenue: float
    nwc_pct_revenue: float         # NWC as % of the change in revenue
    fee_pct: float = 0.02          # transaction fees as % of purchase EV

    def __post_init__(self):
        if len(self.revenue_growth) < 1:
            raise ValueError("need at least one projection year")
        if self.revenue0 <= 0 or self.ebitda0 <= 0:
            raise ValueError("revenue0 and ebitda0 must be positive")
        if self.entry_multiple <= 0 or self.exit_multiple <= 0:
            raise ValueError("multiples must be positive")
        if not 0 <= self.leverage * self.ebitda0 <= self.entry_multiple * self.ebitda0:
            raise ValueError("debt must be between zero and the purchase EV")


@dataclass(frozen=True)
class SourcesUses:
    purchase_ev: float
    fees: float
    total_uses: float
    debt: float
    sponsor_equity: float
    equity_pct: float


@dataclass(frozen=True)
class LBOResult:
    years: np.ndarray
    revenue: np.ndarray
    ebitda: np.ndarray
    interest: np.ndarray
    net_income: np.ndarray
    free_cash_flow: np.ndarray
    debt: np.ndarray
    cash: np.ndarray
    net_debt: np.ndarray
    leverage_path: np.ndarray       # net debt / EBITDA each year
    exit_ev: float
    exit_equity: float
    sources_uses: SourcesUses
    moic: float
    irr: float


def sources_and_uses(inp: LBOInputs) -> SourcesUses:
    purchase_ev = inp.entry_multiple * inp.ebitda0
    fees = inp.fee_pct * purchase_ev
    total = purchase_ev + fees
    debt = inp.leverage * inp.ebitda0
    equity = total - debt
    return SourcesUses(
        purchase_ev=purchase_ev,
        fees=fees,
        total_uses=total,
        debt=debt,
        sponsor_equity=equity,
        equity_pct=equity / total,
    )


def run(inp: LBOInputs) -> LBOResult:
    su = sources_and_uses(inp)
    n = len(inp.revenue_growth)
    growth = np.asarray(inp.revenue_growth, dtype=float)

    revenue = np.zeros(n)
    ebitda = np.zeros(n)
    interest = np.zeros(n)
    net_income = np.zeros(n)
    fcf = np.zeros(n)
    debt = np.zeros(n)
    cash = np.zeros(n)

    prev_rev, prev_debt, prev_cash = inp.revenue0, su.debt, 0.0
    for t in range(n):
        rev = prev_rev * (1 + growth[t])
        e = rev * inp.ebitda_margin
        da = rev * inp.da_pct_revenue
        intr = prev_debt * inp.interest_rate
        ebt = e - da - intr
        tax = max(ebt, 0.0) * inp.tax_rate
        ni = ebt - tax
        capex = rev * inp.capex_pct_revenue
        d_nwc = (rev - prev_rev) * inp.nwc_pct_revenue
        f = ni + da - capex - d_nwc

        # Sweep: repay debt first; any surplus after the debt is gone accumulates as cash.
        new_debt = prev_debt - f
        if new_debt >= 0:
            new_debt_bal, new_cash = new_debt, prev_cash
        else:
            new_debt_bal, new_cash = 0.0, prev_cash + (-new_debt)

        revenue[t], ebitda[t], interest[t] = rev, e, intr
        net_income[t], fcf[t] = ni, f
        debt[t], cash[t] = new_debt_bal, new_cash
        prev_rev, prev_debt, prev_cash = rev, new_debt_bal, new_cash

    net_debt = debt - cash
    leverage_path = net_debt / ebitda
    exit_ev = inp.exit_multiple * ebitda[-1]
    exit_equity = exit_ev - net_debt[-1]
    moic = exit_equity / su.sponsor_equity if su.sponsor_equity > 0 else float("nan")
    irr = moic ** (1 / n) - 1 if moic > 0 else -1.0

    return LBOResult(
        years=np.arange(1, n + 1),
        revenue=revenue,
        ebitda=ebitda,
        interest=interest,
        net_income=net_income,
        free_cash_flow=fcf,
        debt=debt,
        cash=cash,
        net_debt=net_debt,
        leverage_path=leverage_path,
        exit_ev=float(exit_ev),
        exit_equity=float(exit_equity),
        sources_uses=su,
        moic=float(moic),
        irr=float(irr),
    )


def returns_sensitivity(inp: LBOInputs, exit_multiples, entry_multiples) -> np.ndarray:
    """IRR grid over exit multiple (columns) and entry multiple (rows)."""
    grid = np.full((len(entry_multiples), len(exit_multiples)), np.nan)
    for i, em in enumerate(entry_multiples):
        for j, xm in enumerate(exit_multiples):
            params = dict(inp.__dict__)
            params.update(entry_multiple=float(em), exit_multiple=float(xm))
            try:
                grid[i, j] = run(LBOInputs(**params)).irr
            except ValueError:
                pass
    return grid
