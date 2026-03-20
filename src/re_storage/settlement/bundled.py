"""
Option 1: Bundled Discount PPA settlement.

Calculates hourly revenue as delivered energy × EVN tariff × (1 - discount).
Mirrors Excel Financial!F68 Year 1 revenue computation.

Excel source: Financial!F64–F70, Assumption!Q30
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.types import TimePeriod


def calculate_bundled_revenue(
    direct_pv_kw: pd.Series,
    discharged_kw: pd.Series,
    time_period: pd.Series,
    tariff_rates: dict[TimePeriod, float],
    discount_pct: float = 0.15,
) -> pd.Series:
    """
    Calculate hourly revenue for Bundled Discount PPA (Option 1).

    Revenue = (direct_pv_kw + discharged_kw) × tariff_rate × (1 - discount_pct)

    The delivered energy includes all clean energy the customer receives:
    direct PV consumption plus BESS discharge. The discount reflects the
    customer's negotiated reduction on the prevailing EVN retail tariff.

    Excel source: Financial!F64–F70, Assumption!Q30 (15% discount)

    Args:
        direct_pv_kw: Hourly direct PV to load (kW = kWh per 1-h step).
        discharged_kw: Hourly BESS discharge to load (kW).
        time_period: Hourly tariff period classification.
        tariff_rates: Dict mapping TimePeriod → rate (USD/kWh).
        discount_pct: Bundled discount percentage (Assumption!Q30, default 15%).

    Returns:
        Series of hourly bundled revenue (USD).
    """
    delivered_kw = direct_pv_kw + discharged_kw
    tariff_series = time_period.map(tariff_rates)
    return delivered_kw * tariff_series * (1.0 - discount_pct)
