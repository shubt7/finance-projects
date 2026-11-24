"""Precedent transactions: multiple statistics and implied valuation ranges."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MultipleStats:
    count: int
    low: float
    p25: float
    median: float
    mean: float
    p75: float
    high: float


@dataclass(frozen=True)
class ImpliedValue:
    low: float
    mid: float
    high: float


def summarise(multiples) -> MultipleStats:
    m = np.asarray(multiples, dtype=float)
    m = m[np.isfinite(m) & (m > 0)]
    if m.size < 3:
        raise ValueError("need at least three valid transaction multiples")
    p25, med, p75 = np.percentile(m, [25, 50, 75])
    return MultipleStats(
        count=int(m.size),
        low=float(m.min()),
        p25=float(p25),
        median=float(med),
        mean=float(m.mean()),
        p75=float(p75),
        high=float(m.max()),
    )


def implied_value(multiples, metric: float) -> ImpliedValue:
    """Enterprise value range from the interquartile range of transaction multiples."""
    s = summarise(multiples)
    return ImpliedValue(low=s.p25 * metric, mid=s.median * metric, high=s.p75 * metric)
