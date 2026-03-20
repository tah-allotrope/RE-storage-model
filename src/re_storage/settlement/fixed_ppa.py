"""
Option 4: Fixed PPA with EVN settlement.

Calculates hourly revenue as generation × fixed_price adjusted for
curtailment and transmission losses. Mirrors Excel Financial!F74.

Excel source: Financial!F84–F90, Assumption!Q61
"""

from __future__ import annotations

import pandas as pd


def calculate_fixed_ppa_revenue(
    solar_gen_kw: pd.Series,
    fixed_price_usd_per_mwh: float = 70.0,
    curtailment_pct: float = 0.0,
    tx_loss_pct: float = 0.0,
) -> pd.Series:
    """
    Calculate hourly revenue for Fixed PPA with EVN (Option 4).

    Revenue = solar_gen_kWh × fixed_price_usd_per_kwh
              × (1 - curtailment_pct) × (1 - tx_loss_pct)

    For a 1-hour timestep kW equals kWh, so kW is used directly.

    Excel source: Financial!F84–F90, Assumption!Q61 ($70/MWh fixed)

    Args:
        solar_gen_kw: Hourly solar generation (kW, equals kWh per 1-h step).
        fixed_price_usd_per_mwh: Fixed PPA price in USD/MWh (Assumption!Q61).
        curtailment_pct: Generation curtailment fraction (0–1).
        tx_loss_pct: Transmission loss fraction (0–1).

    Returns:
        Series of hourly fixed PPA revenue (USD).
    """
    fixed_price_usd_per_kwh = fixed_price_usd_per_mwh / 1000.0
    net_factor = (1.0 - curtailment_pct) * (1.0 - tx_loss_pct)
    return solar_gen_kw * fixed_price_usd_per_kwh * net_factor
