"""
Option 2: Separate PV + BESS discount PPA settlement.

Calculates hourly revenue with independent discount rates for the PV and
BESS components. Mirrors Excel Financial!F80 Year 1 revenue computation.

Excel source: Financial!F71–F83, Assumption!Q33 (PV disc), Q34 (BESS disc)
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.types import TimePeriod


def calculate_separate_revenue(
    direct_pv_kw: pd.Series,
    discharged_kw: pd.Series,
    time_period: pd.Series,
    tariff_rates: dict[TimePeriod, float],
    pv_discount_pct: float = 0.05,
    bess_discount_pct: float = 0.05,
) -> pd.Series:
    """
    Calculate hourly revenue for Separate PV + BESS PPA (Option 2).

    PV revenue   = direct_pv_kw  × tariff × (1 - pv_discount_pct)
    BESS revenue = discharged_kw × tariff × (1 - bess_discount_pct)
    Total        = PV revenue + BESS revenue

    Excel source: Financial!F71–F83, Assumption!Q33 & Q34

    Args:
        direct_pv_kw: Hourly direct PV to load (kW = kWh per 1-h step).
        discharged_kw: Hourly BESS discharge to load (kW).
        time_period: Hourly tariff period classification.
        tariff_rates: Dict mapping TimePeriod → rate (USD/kWh).
        pv_discount_pct: PV discount percentage (Assumption!Q33, default 5%).
        bess_discount_pct: BESS discount percentage (Assumption!Q34, default 5%).

    Returns:
        Series of hourly separate-pricing revenue (USD).
    """
    tariff_series = time_period.map(tariff_rates)
    pv_revenue = direct_pv_kw * tariff_series * (1.0 - pv_discount_pct)
    bess_revenue = discharged_kw * tariff_series * (1.0 - bess_discount_pct)
    return pv_revenue + bess_revenue
