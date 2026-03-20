"""
Demand charge savings calculation.

Computes annual savings from the monthly peak demand reduction achieved by
the BESS (peak shaving), expressed in USD.

Excel source: Financial!F54, F59, Assumption!O13, Other Input!B13
"""

from __future__ import annotations

import pandas as pd


def calculate_annual_demand_savings(
    monthly_data: pd.DataFrame,
    cp_demand_vnd_per_kw: float,
    exchange_rate_usd_vnd: float,
) -> float:
    """
    Calculate annual demand charge savings (USD).

    Savings = Σ_months [(baseline_peak_kw - post_re_peak_kw) × Cp_demand] / FX

    For 1-component tariff projects (current test project), Cp_demand = 0,
    so savings are zero regardless of peak reduction.

    Excel source: Financial!F59, Assumption!O13

    Args:
        monthly_data: Monthly aggregation DataFrame.  Must contain columns
            'baseline_peak_kw' and 'peak_demand_after_re_kw'.
        cp_demand_vnd_per_kw: Capacity demand charge (VND/kW).
            Zero for 1-component tariff.
        exchange_rate_usd_vnd: VND per USD exchange rate.

    Returns:
        Annual demand charge savings (USD).  Zero when cp_demand = 0.
    """
    if cp_demand_vnd_per_kw <= 0 or exchange_rate_usd_vnd <= 0:
        return 0.0

    required = {"baseline_peak_kw", "peak_demand_after_re_kw"}
    if not required.issubset(monthly_data.columns):
        return 0.0

    peak_reduction_kw = (
        monthly_data["baseline_peak_kw"] - monthly_data["peak_demand_after_re_kw"]
    ).clip(lower=0.0)
    savings_vnd = peak_reduction_kw.sum() * cp_demand_vnd_per_kw
    return float(savings_vnd / exchange_rate_usd_vnd)
