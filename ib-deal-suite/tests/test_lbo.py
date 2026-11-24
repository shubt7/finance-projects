import math

import numpy as np
import pytest

from dealsuite import LBOInputs, returns_sensitivity, run, sources_and_uses


def _base(**overrides):
    base = dict(
        revenue0=500.0, ebitda0=100.0, revenue_growth=(0.0,) * 5, ebitda_margin=0.2,
        entry_multiple=10.0, exit_multiple=10.0, leverage=5.0, interest_rate=0.0,
        tax_rate=0.0, da_pct_revenue=0.0, capex_pct_revenue=0.0, nwc_pct_revenue=0.0,
        fee_pct=0.0,
    )
    base.update(overrides)
    return LBOInputs(**base)


def test_sources_equal_uses():
    su = sources_and_uses(_base(fee_pct=0.02))
    assert su.debt + su.sponsor_equity == pytest.approx(su.total_uses)
    assert su.purchase_ev == pytest.approx(1000.0)
    assert su.fees == pytest.approx(20.0)


def test_flat_case_debt_fully_repaid_and_known_returns():
    # EBITDA 100 each year, no interest/tax/capex: FCF = 100/yr, so 500 of debt is gone by year 5.
    res = run(_base())
    assert res.debt[-1] == pytest.approx(0.0, abs=1e-9)
    assert res.cash[-1] == pytest.approx(0.0, abs=1e-9)
    assert res.exit_equity == pytest.approx(1000.0)
    assert res.moic == pytest.approx(2.0)
    assert res.irr == pytest.approx(2.0 ** (1 / 5) - 1)


def test_debt_never_negative_and_cash_builds_after_payoff():
    res = run(_base(leverage=1.0, revenue_growth=(0.1,) * 5))
    assert np.all(res.debt >= -1e-12)
    assert np.all(res.cash >= -1e-12)
    assert res.cash[-1] > 0


def test_irr_matches_moic_identity():
    res = run(_base(interest_rate=0.07, tax_rate=0.25, da_pct_revenue=0.03, capex_pct_revenue=0.04))
    assert res.irr == pytest.approx(res.moic ** (1 / 5) - 1)


def test_higher_exit_multiple_raises_irr():
    grid = returns_sensitivity(_base(), exit_multiples=[8.0, 10.0, 12.0], entry_multiples=[10.0])
    assert grid[0, 0] < grid[0, 1] < grid[0, 2]


def test_rejects_debt_above_purchase_price():
    with pytest.raises(ValueError):
        _base(leverage=11.0)
