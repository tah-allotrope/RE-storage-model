"""
Physics module: Energy simulation engine.

This module implements the core physics of solar PV generation and
battery energy storage dispatch. It enforces the "Physics First"
principle by validating energy balance before any financial calculations.

Submodules:
    solar: PV generation scaling and consumption calculations
    battery: BESS dispatch logic and state of charge tracking
    balance: Energy balance validation

Key Invariants:
    1. Energy is conserved: Solar = Direct + Charged + Surplus
    2. SoC stays within bounds: 0 <= SoC <= Usable_Capacity
    3. Power respects equipment ratings
"""

from re_storage.physics.balance import (
    validate_energy_balance,
    validate_soc_bounds,
    validate_power_rating,
)
from re_storage.physics.solar import (
    scale_generation,
    calculate_direct_pv_consumption,
    calculate_surplus_generation,
)
from re_storage.physics.battery import (
    calculate_charge_limit,
    calculate_pv_to_bess,
    evaluate_discharge_permission,
    calculate_discharge_power,
    update_soc,
    BatteryState,
)

__all__ = [
    # Solar
    "scale_generation",
    "calculate_direct_pv_consumption",
    "calculate_surplus_generation",
    # Battery
    "calculate_charge_limit",
    "calculate_pv_to_bess",
    "evaluate_discharge_permission",
    "calculate_discharge_power",
    "update_soc",
    "BatteryState",
    # Balance
    "validate_energy_balance",
    "validate_soc_bounds",
    "validate_power_rating",
]
