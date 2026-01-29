"""
Solar PV generation calculations.

This module handles:
1. Scaling simulation profiles to actual installed capacity
2. Calculating direct PV consumption by load
3. Calculating surplus generation available for export

Reference: model_architecture.md §A.1 (Solar Generation Scaling)
"""

import logging
from typing import TypeAlias

import numpy as np
import pandas as pd

from re_storage.core.types import PowerKW, EnergyKWH, Ratio

logger = logging.getLogger(__name__)

# Type alias for array-like inputs
ArrayLike: TypeAlias = np.ndarray | pd.Series | list[float]


def scale_generation(
    simulation_profile_kw: ArrayLike,
    scale_factor: Ratio,
) -> np.ndarray:
    """
    Scale simulation profile to match actual installed capacity.

    The raw PV simulation (from PVsyst or similar) is generated for a
    reference capacity. This function scales it to the actual installed
    capacity using Output_Scale_Factor.

    Formula (from Calc!Col F):
        SolarGen_kW = SimulationProfile_kW × Output_Scale_Factor

    Args:
        simulation_profile_kw: Raw PV output from simulation tool (kW).
            Typically 8760 or 8784 hourly values.
        scale_factor: Ratio of actual to simulation capacity.
            = Actual_installation_capacity / Simulation_capacity
            Typically close to 1.0 unless simulation was run at
            different capacity than final installation.

    Returns:
        Scaled solar generation array (kW), same length as input.

    Raises:
        ValueError: If scale_factor is not positive.

    Example:
        >>> profile = [100, 200, 300, 200, 100]  # 5 hours of simulation
        >>> scaled = scale_generation(profile, scale_factor=1.1)
        >>> scaled  # Each value increased by 10%
        array([110., 220., 330., 220., 110.])
    """
    if scale_factor <= 0:
        raise ValueError(f"scale_factor must be positive, got {scale_factor}")

    profile = np.asarray(simulation_profile_kw, dtype=np.float64)
    return profile * scale_factor


def calculate_direct_pv_consumption(
    solar_gen_kw: PowerKW,
    load_kw: PowerKW,
    pv_to_bess_kw: PowerKW,
) -> PowerKW:
    """
    Calculate direct PV consumption by load (excluding battery diversion).

    This is the portion of solar generation that directly serves the load,
    after subtracting any power diverted to charge the battery.

    Formula (from Calc!Col I):
        DirectPVConsumption_kW = MIN(Load, MAX(Solar - PV2BESS, 0))

    The MIN ensures we don't consume more than the load requires.
    The MAX ensures we don't get negative values if PV2BESS > Solar.

    Args:
        solar_gen_kw: Total solar generation this timestep (kW).
        load_kw: Site electrical load this timestep (kW).
        pv_to_bess_kw: Power diverted from PV to battery charging (kW).

    Returns:
        Direct PV power consumed by load (kW).

    Raises:
        ValueError: If any input is negative.

    Example:
        >>> calculate_direct_pv_consumption(
        ...     solar_gen_kw=100,
        ...     load_kw=80,
        ...     pv_to_bess_kw=30
        ... )
        70.0  # 100 - 30 = 70 available, but load only needs 80 → 70
    """
    if solar_gen_kw < 0:
        raise ValueError(f"solar_gen_kw cannot be negative: {solar_gen_kw}")
    if load_kw < 0:
        raise ValueError(f"load_kw cannot be negative: {load_kw}")
    if pv_to_bess_kw < 0:
        raise ValueError(f"pv_to_bess_kw cannot be negative: {pv_to_bess_kw}")

    available_for_load = max(solar_gen_kw - pv_to_bess_kw, 0.0)
    return min(load_kw, available_for_load)


def calculate_direct_pv_consumption_vectorized(
    solar_gen_kw: ArrayLike,
    load_kw: ArrayLike,
    pv_to_bess_kw: ArrayLike,
) -> np.ndarray:
    """
    Vectorized version of calculate_direct_pv_consumption for full time series.

    Processes entire 8760-hour arrays efficiently using numpy operations.

    Args:
        solar_gen_kw: Solar generation array (kW).
        load_kw: Load array (kW).
        pv_to_bess_kw: PV to battery diversion array (kW).

    Returns:
        Direct PV consumption array (kW).

    Raises:
        ValueError: If any array contains negative values.
    """
    solar = np.asarray(solar_gen_kw, dtype=np.float64)
    load = np.asarray(load_kw, dtype=np.float64)
    pv2bess = np.asarray(pv_to_bess_kw, dtype=np.float64)

    if np.any(solar < 0):
        raise ValueError("solar_gen_kw contains negative values")
    if np.any(load < 0):
        raise ValueError("load_kw contains negative values")
    if np.any(pv2bess < 0):
        raise ValueError("pv_to_bess_kw contains negative values")

    available_for_load = np.maximum(solar - pv2bess, 0.0)
    return np.minimum(load, available_for_load)


def calculate_surplus_generation(
    solar_gen_kw: PowerKW,
    direct_consumption_kw: PowerKW,
    pv_charged_kw: PowerKW,
) -> PowerKW:
    """
    Calculate surplus solar generation available for grid export.

    Surplus is solar that is neither consumed by load nor stored in battery.
    This may be exported to grid under DPPA or curtailed.

    Formula (from Calc!Col Z logic):
        Surplus_kW = Solar - DirectConsumption - PVCharged

    Args:
        solar_gen_kw: Total solar generation (kW).
        direct_consumption_kw: PV consumed directly by load (kW).
        pv_charged_kw: PV power going to battery charging (kW).

    Returns:
        Surplus generation (kW). Should be >= 0 if inputs are valid.

    Raises:
        ValueError: If any input is negative or if result would be negative.

    Note:
        A negative result indicates an energy balance error - the model
        is consuming/charging more than was generated.
    """
    if solar_gen_kw < 0:
        raise ValueError(f"solar_gen_kw cannot be negative: {solar_gen_kw}")
    if direct_consumption_kw < 0:
        raise ValueError(f"direct_consumption_kw cannot be negative: {direct_consumption_kw}")
    if pv_charged_kw < 0:
        raise ValueError(f"pv_charged_kw cannot be negative: {pv_charged_kw}")

    surplus = solar_gen_kw - direct_consumption_kw - pv_charged_kw

    if surplus < -0.001:  # Small tolerance for floating point
        raise ValueError(
            f"Negative surplus ({surplus:.4f} kW) indicates energy balance error. "
            f"Solar={solar_gen_kw}, Direct={direct_consumption_kw}, Charged={pv_charged_kw}"
        )

    return max(surplus, 0.0)


def calculate_surplus_generation_vectorized(
    solar_gen_kw: ArrayLike,
    direct_consumption_kw: ArrayLike,
    pv_charged_kw: ArrayLike,
    tolerance: float = 0.001,
) -> np.ndarray:
    """
    Vectorized version of calculate_surplus_generation.

    Args:
        solar_gen_kw: Solar generation array (kW).
        direct_consumption_kw: Direct consumption array (kW).
        pv_charged_kw: PV charging array (kW).
        tolerance: Acceptable negative threshold for floating point errors.

    Returns:
        Surplus generation array (kW).

    Raises:
        ValueError: If any timestep has surplus below -tolerance.
    """
    solar = np.asarray(solar_gen_kw, dtype=np.float64)
    direct = np.asarray(direct_consumption_kw, dtype=np.float64)
    charged = np.asarray(pv_charged_kw, dtype=np.float64)

    surplus = solar - direct - charged

    negative_mask = surplus < -tolerance
    if np.any(negative_mask):
        bad_indices = np.where(negative_mask)[0]
        first_bad = bad_indices[0]
        raise ValueError(
            f"Negative surplus at {len(bad_indices)} timesteps. "
            f"First violation at index {first_bad}: surplus={surplus[first_bad]:.4f} kW"
        )

    return np.maximum(surplus, 0.0)
