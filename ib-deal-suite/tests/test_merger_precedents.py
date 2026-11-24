import numpy as np
import pytest

from dealsuite import MergerInputs, accretion_by_synergies, analyse, implied_value, summarise


def _merger(**overrides):
    base = dict(
        acquirer_price=50.0, acquirer_shares=100.0, acquirer_net_income=200.0,
        target_net_income=20.0, purchase_equity_value=500.0, stock_pct=0.0,
        debt_rate=0.06, synergies_pre_tax=0.0, tax_rate=0.25,
    )
    base.update(overrides)
    return MergerInputs(**base)


def test_all_cash_no_synergies_matches_hand_calculation():
    res = analyse(_merger())
    # Interest after tax: 500 * 6% * 0.75 = 22.5. PF NI = 200 + 20 - 22.5 = 197.5. Shares unchanged.
    assert res.pro_forma_net_income == pytest.approx(197.5)
    assert res.pro_forma_eps == pytest.approx(1.975)
    assert res.standalone_eps == pytest.approx(2.0)
    assert res.accretion_pct == pytest.approx(-0.0125)


def test_breakeven_synergies_give_zero_accretion():
    base = _merger()
    be = analyse(base).breakeven_synergies_pre_tax
    res = analyse(_merger(synergies_pre_tax=be))
    assert res.accretion_pct == pytest.approx(0.0, abs=1e-9)


def test_stock_deal_issues_shares_at_acquirer_price():
    res = analyse(_merger(stock_pct=1.0))
    assert res.new_shares == pytest.approx(500.0 / 50.0)
    assert res.new_debt == pytest.approx(0.0)


def test_accretion_increases_with_synergies():
    levels = np.array([0.0, 10.0, 20.0, 40.0])
    acc = accretion_by_synergies(_merger(), levels)
    assert np.all(np.diff(acc) > 0)


def test_precedent_stats_are_ordered_and_ignore_bad_values():
    s = summarise([7.5, 8.0, np.nan, 9.0, 10.0, 11.5, -1.0, 12.0])
    assert s.count == 6
    assert s.low <= s.p25 <= s.median <= s.p75 <= s.high
    assert s.median == pytest.approx(9.5)


def test_implied_value_scales_with_metric():
    v = implied_value([8.0, 9.0, 10.0, 11.0], metric=100.0)
    assert v.low <= v.mid <= v.high
    assert v.mid == pytest.approx(950.0)
