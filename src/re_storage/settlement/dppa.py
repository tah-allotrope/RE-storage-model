"""
DPPA/CfD settlement calculations.

This module implements the regulatory sidecar for Vietnam's DPPA mechanism,
including market revenue and Contract-for-Difference (CfD) settlements.
"""

from __future__ import annotations

import logging

import pandas as pd

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import HourlyTimeSeries
from re_storage.inputs.schemas import SystemAssumptions

logger = logging.getLogger(__name__)


def calculate_delivered_re(
    net_gen_kwh: float,
    k_factor: float,
    kpp: float,
    delta: float = 1.0,
) -> float:
    """
    Calculate delivered renewable energy after loss adjustments.

    The DPPA model applies k_factor and kpp to net generation to reflect
    delivery and pricing adjustments, consistent with DPPA sheet logic.

    Args:
        net_gen_kwh: Net renewable generation available for DPPA (kWh).
        k_factor: Loss adjustment factor (> 0).
        kpp: Price adjustment coefficient (> 0).
        delta: Settlement interval factor (default 1.0).

    Returns:
        Delivered renewable energy (kWh).

    Raises:
        ValueError: If net_gen_kwh is negative or factors are non-positive.
    """
    if net_gen_kwh < 0:
        raise ValueError(f"net_gen_kwh cannot be negative: {net_gen_kwh}")
    if k_factor <= 0:
        raise ValueError(f"k_factor must be positive: {k_factor}")
    if kpp <= 0:
        raise ValueError(f"kpp must be positive: {kpp}")
    if delta <= 0:
        raise ValueError(f"delta must be positive: {delta}")

    return (net_gen_kwh / (k_factor * kpp)) * delta


def calculate_consumed_re(delivered_re_kwh: float, load_kwh: float) -> float:
    """
    Calculate consumed renewable energy capped by load.

    Args:
        delivered_re_kwh: Delivered renewable energy (kWh).
        load_kwh: Site load (kWh).

    Returns:
        Consumed renewable energy (kWh).

    Raises:
        ValueError: If delivered_re_kwh or load_kwh is negative.
    """
    if delivered_re_kwh < 0:
        raise ValueError(f"delivered_re_kwh cannot be negative: {delivered_re_kwh}")
    if load_kwh < 0:
        raise ValueError(f"load_kwh cannot be negative: {load_kwh}")

    return min(delivered_re_kwh, load_kwh)


def calculate_market_revenue(net_gen_kwh: float, fmp_usd_per_kwh: float) -> float:
    """
    Calculate market revenue from net generation and spot price.

    Args:
        net_gen_kwh: Net generation (kWh).
        fmp_usd_per_kwh: Spot market price ($/kWh).

    Returns:
        Market revenue (USD).

    Raises:
        ValueError: If net_gen_kwh is negative.
    """
    if net_gen_kwh < 0:
        raise ValueError(f"net_gen_kwh cannot be negative: {net_gen_kwh}")

    return net_gen_kwh * fmp_usd_per_kwh


def calculate_cfd_settlement(
    consumed_re_kwh: float,
    strike_price_usd_per_kwh: float,
    spot_price_usd_per_kwh: float,
) -> float:
    """
    Calculate Contract-for-Difference (CfD) settlement amount.

    Args:
        consumed_re_kwh: Renewable energy consumed (kWh).
        strike_price_usd_per_kwh: Fixed strike price ($/kWh).
        spot_price_usd_per_kwh: Spot price ($/kWh).

    Returns:
        CfD settlement (USD). Positive if strike > spot.

    Raises:
        ValueError: If consumed_re_kwh is negative.
    """
    if consumed_re_kwh < 0:
        raise ValueError(f"consumed_re_kwh cannot be negative: {consumed_re_kwh}")

    return consumed_re_kwh * (strike_price_usd_per_kwh - spot_price_usd_per_kwh)


def calculate_total_dppa_revenue(market_revenue_usd: float, cfd_settlement_usd: float) -> float:
    """
    Calculate total DPPA revenue.

    Args:
        market_revenue_usd: Revenue from market sales (USD).
        cfd_settlement_usd: CfD settlement (USD).

    Returns:
        Total DPPA revenue (USD).
    """
    return market_revenue_usd + cfd_settlement_usd


def calculate_dppa_revenue(
    hourly_data: HourlyTimeSeries,
    assumptions: SystemAssumptions,
    net_gen_column: str = "net_gen_for_dppa_kwh",
    load_column: str = "load_kwh",
    fmp_column: str = "fmp_usd_per_kwh",
    delta: float = 1.0,
) -> pd.DataFrame:
    """
    Calculate DPPA revenue columns for each hourly timestep.

    Args:
        hourly_data: Hourly time series with net generation and load columns.
        assumptions: System assumptions including DPPA parameters.
        net_gen_column: Column name for net DPPA generation (kWh).
        load_column: Column name for load (kWh).
        fmp_column: Column name for market price ($/kWh).
        delta: Settlement interval factor (default 1.0).

    Returns:
        New DataFrame with DPPA revenue columns appended.

    Raises:
        InputValidationError: If required columns are missing or values are invalid.
    """
    required = {net_gen_column, load_column, fmp_column}
    missing = required - set(hourly_data.columns)
    if missing:
        raise InputValidationError(f"Missing required columns for DPPA: {sorted(missing)}")

    if (hourly_data[net_gen_column] < 0).any():
        raise InputValidationError("net_gen_for_dppa_kwh contains negative values.")
    if (hourly_data[load_column] < 0).any():
        raise InputValidationError("load_kwh contains negative values.")

    result = hourly_data.copy()

    if not assumptions.dppa_enabled:
        logger.warning(
            "DPPA module is DISABLED (dppa_enabled=False). All DPPA revenue will be zero."
        )
        result["delivered_re_kwh"] = 0.0
        result["consumed_re_kwh"] = 0.0
        result["market_revenue_usd"] = 0.0
        result["cfd_settlement_usd"] = 0.0
        result["total_dppa_revenue_usd"] = 0.0
        return result

    delivered_re_kwh = (
        result[net_gen_column] / (assumptions.k_factor * assumptions.kpp)
    ) * delta
    consumed_re_kwh = delivered_re_kwh.where(
        delivered_re_kwh <= result[load_column], result[load_column]
    )
    market_revenue_usd = result[net_gen_column] * result[fmp_column]
    cfd_settlement_usd = consumed_re_kwh * (
        assumptions.strike_price_usd_per_kwh - result[fmp_column]
    )

    result["delivered_re_kwh"] = delivered_re_kwh
    result["consumed_re_kwh"] = consumed_re_kwh
    result["market_revenue_usd"] = market_revenue_usd
    result["cfd_settlement_usd"] = cfd_settlement_usd
    result["total_dppa_revenue_usd"] = market_revenue_usd + cfd_settlement_usd

    return result
