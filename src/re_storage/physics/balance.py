"""
Energy balance validation.

This module enforces the "Physics First" principle by validating that
energy is conserved at every timestep before proceeding to financial
calculations.

Key Invariants:
    1. Solar energy balance: Solar = Direct + Charged + Surplus
    2. SoC bounds: 0 <= SoC <= Usable_Capacity
    3. Power rating limits: Power <= Equipment_Rating

Reference: model_architecture.md Risk 6 (Balance Check Column)
"""

import logging

import numpy as np

from re_storage.core.exceptions import (
    EnergyBalanceError,
    InsufficientCapacityError,
    SoCBoundsError,
)
from re_storage.core.types import EnergyKWH, PowerKW

logger = logging.getLogger(__name__)


def validate_energy_balance(
    solar_gen_kwh: EnergyKWH,
    direct_consumption_kwh: EnergyKWH,
    charged_kwh: EnergyKWH,
    surplus_kwh: EnergyKWH,
    tolerance: float = 0.001,
    timestep: int | None = None,
) -> None:
    """
    Validate that solar energy is fully accounted for.

    This is the Python equivalent of Calc!Col R (Balance_Check).
    The formula checks: Solar = Direct + Charged + Surplus

    This validation is CRITICAL for model integrity. If energy doesn't
    balance, all financial calculations downstream will be incorrect.

    Args:
        solar_gen_kwh: Total solar energy generated this timestep (kWh).
        direct_consumption_kwh: Energy consumed directly by load (kWh).
        charged_kwh: Energy stored in battery (kWh).
        surplus_kwh: Energy exported to grid or curtailed (kWh).
        tolerance: Acceptable imbalance for floating point errors (kWh).
            Default 0.001 kWh = 1 Wh, negligible for utility-scale.
        timestep: Optional timestep index for error reporting.

    Raises:
        EnergyBalanceError: If |Solar - (Direct + Charged + Surplus)| > tolerance.

    Example:
        >>> validate_energy_balance(
        ...     solar_gen_kwh=100.0,
        ...     direct_consumption_kwh=60.0,
        ...     charged_kwh=30.0,
        ...     surplus_kwh=10.0,
        ... )  # Passes: 100 = 60 + 30 + 10

        >>> validate_energy_balance(
        ...     solar_gen_kwh=100.0,
        ...     direct_consumption_kwh=60.0,
        ...     charged_kwh=30.0,
        ...     surplus_kwh=20.0,
        ... )  # Raises: 100 ≠ 60 + 30 + 20 = 110
    """
    total_accounted = direct_consumption_kwh + charged_kwh + surplus_kwh
    imbalance = solar_gen_kwh - total_accounted

    if abs(imbalance) > tolerance:
        ts_info = f" at timestep {timestep}" if timestep is not None else ""
        raise EnergyBalanceError(
            f"Energy balance failed{ts_info}: {imbalance:.6f} kWh imbalance. "
            f"Solar={solar_gen_kwh:.4f}, Direct={direct_consumption_kwh:.4f}, "
            f"Charged={charged_kwh:.4f}, Surplus={surplus_kwh:.4f}. "
            f"Expected sum={total_accounted:.4f}",
            imbalance_kwh=imbalance,
            timestep=timestep,
        )


def validate_energy_balance_vectorized(
    solar_gen_kwh: np.ndarray,
    direct_consumption_kwh: np.ndarray,
    charged_kwh: np.ndarray,
    surplus_kwh: np.ndarray,
    tolerance: float = 0.001,
) -> None:
    """
    Vectorized validation of energy balance across all timesteps.

    Checks all 8760 timesteps in a single pass and reports the first
    violation found.

    Args:
        solar_gen_kwh: Solar generation array (kWh).
        direct_consumption_kwh: Direct consumption array (kWh).
        charged_kwh: Energy charged to battery array (kWh).
        surplus_kwh: Surplus generation array (kWh).
        tolerance: Acceptable imbalance per timestep (kWh).

    Raises:
        EnergyBalanceError: If any timestep violates balance constraint.
    """
    total_accounted = direct_consumption_kwh + charged_kwh + surplus_kwh
    imbalance = solar_gen_kwh - total_accounted

    violations = np.abs(imbalance) > tolerance
    if np.any(violations):
        violation_count = np.sum(violations)
        first_idx = int(np.argmax(violations))
        max_imbalance = float(np.max(np.abs(imbalance)))

        raise EnergyBalanceError(
            f"Energy balance failed at {violation_count} timesteps. "
            f"First violation at index {first_idx}: {imbalance[first_idx]:.6f} kWh. "
            f"Maximum imbalance: {max_imbalance:.6f} kWh.",
            imbalance_kwh=max_imbalance,
            timestep=first_idx,
        )


def validate_soc_bounds(
    soc_kwh: EnergyKWH,
    max_capacity_kwh: EnergyKWH,
    timestep: int | None = None,
    tolerance: float = 0.001,
) -> None:
    """
    Validate that State of Charge is within valid bounds.

    Battery SoC must satisfy: 0 <= SoC <= Usable_Capacity

    This constraint is physically meaningful:
    - SoC < 0: Battery has "negative" energy (impossible)
    - SoC > max: Battery holds more than capacity (impossible)

    Args:
        soc_kwh: Current state of charge (kWh).
        max_capacity_kwh: Usable battery capacity (kWh).
        timestep: Optional timestep index for error reporting.
        tolerance: Acceptable overshoot for floating point errors (kWh).

    Raises:
        SoCBoundsError: If SoC is outside valid bounds.

    Example:
        >>> validate_soc_bounds(soc_kwh=50.0, max_capacity_kwh=100.0)  # OK
        >>> validate_soc_bounds(soc_kwh=-1.0, max_capacity_kwh=100.0)  # Raises
        >>> validate_soc_bounds(soc_kwh=101.0, max_capacity_kwh=100.0)  # Raises
    """
    ts_info = f" at timestep {timestep}" if timestep is not None else ""

    if soc_kwh < -tolerance:
        raise SoCBoundsError(
            f"Negative SoC{ts_info}: {soc_kwh:.4f} kWh. "
            "Battery cannot have negative energy (over-discharged).",
            soc_kwh=soc_kwh,
            max_capacity_kwh=max_capacity_kwh,
            timestep=timestep,
        )

    if soc_kwh > max_capacity_kwh + tolerance:
        raise SoCBoundsError(
            f"SoC exceeds capacity{ts_info}: {soc_kwh:.4f} > {max_capacity_kwh:.4f} kWh. "
            "Battery cannot hold more than its rated capacity (over-charged).",
            soc_kwh=soc_kwh,
            max_capacity_kwh=max_capacity_kwh,
            timestep=timestep,
        )


def validate_soc_bounds_vectorized(
    soc_kwh: np.ndarray,
    max_capacity_kwh: float,
    tolerance: float = 0.001,
) -> None:
    """
    Vectorized validation of SoC bounds across all timesteps.

    Args:
        soc_kwh: State of charge array (kWh).
        max_capacity_kwh: Usable battery capacity (kWh).
        tolerance: Acceptable bound violation for floating point (kWh).

    Raises:
        SoCBoundsError: If any timestep violates SoC bounds.
    """
    too_low = soc_kwh < -tolerance
    too_high = soc_kwh > max_capacity_kwh + tolerance

    if np.any(too_low):
        first_idx = int(np.argmax(too_low))
        min_soc = float(np.min(soc_kwh))
        raise SoCBoundsError(
            f"Negative SoC at {np.sum(too_low)} timesteps. "
            f"First at index {first_idx}, minimum SoC: {min_soc:.4f} kWh.",
            soc_kwh=min_soc,
            max_capacity_kwh=max_capacity_kwh,
            timestep=first_idx,
        )

    if np.any(too_high):
        first_idx = int(np.argmax(too_high))
        max_soc = float(np.max(soc_kwh))
        raise SoCBoundsError(
            f"SoC exceeds capacity at {np.sum(too_high)} timesteps. "
            f"First at index {first_idx}, maximum SoC: {max_soc:.4f} kWh "
            f"(capacity: {max_capacity_kwh:.4f} kWh).",
            soc_kwh=max_soc,
            max_capacity_kwh=max_capacity_kwh,
            timestep=first_idx,
        )


def validate_power_rating(
    power_kw: PowerKW,
    max_rating_kw: PowerKW,
    equipment_name: str = "equipment",
    timestep: int | None = None,
    tolerance: float = 0.01,
) -> None:
    """
    Validate that power flow does not exceed equipment rating.

    Power flows are constrained by physical equipment:
    - Inverter rating (AC/DC conversion limit)
    - Grid connection (utility interconnection limit)
    - Transformer (kVA rating)

    Args:
        power_kw: Power flow to validate (kW).
        max_rating_kw: Maximum equipment rating (kW).
        equipment_name: Name of equipment for error message.
        timestep: Optional timestep index for error reporting.
        tolerance: Acceptable overshoot percentage (ratio, not %).

    Raises:
        InsufficientCapacityError: If power exceeds rating by more than tolerance.

    Example:
        >>> validate_power_rating(
        ...     power_kw=105.0,
        ...     max_rating_kw=100.0,
        ...     equipment_name="inverter",
        ...     tolerance=0.05,  # 5% acceptable
        ... )  # OK: 105 is within 5% of 100

        >>> validate_power_rating(
        ...     power_kw=120.0,
        ...     max_rating_kw=100.0,
        ...     equipment_name="inverter",
        ...     tolerance=0.05,
        ... )  # Raises: 120 exceeds 100 by 20%
    """
    if max_rating_kw <= 0:
        raise ValueError(f"max_rating_kw must be positive, got {max_rating_kw}")

    allowable_max = max_rating_kw * (1 + tolerance)

    if power_kw > allowable_max:
        ts_info = f" at timestep {timestep}" if timestep is not None else ""
        overage_pct = ((power_kw / max_rating_kw) - 1) * 100

        raise InsufficientCapacityError(
            f"{equipment_name} rating exceeded{ts_info}: "
            f"{power_kw:.2f} kW > {max_rating_kw:.2f} kW ({overage_pct:.1f}% over).",
            requested_kw=power_kw,
            available_kw=max_rating_kw,
        )
