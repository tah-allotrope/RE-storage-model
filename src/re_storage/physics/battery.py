"""
Battery Energy Storage System (BESS) dispatch logic.

This module implements the core battery dispatch algorithms including:
1. Charge limit calculations
2. PV-to-BESS diversion strategies (time window, precharge target)
3. Discharge permission logic (arbitrage, peak shaving)
4. State of Charge (SoC) tracking

Reference: model_architecture.md §A.2, §A.3, §A.4

CRITICAL: The discharge permission logic has 4 overlapping conditions
(Risk 1 from architecture doc). This implementation logs warnings when
multiple conditions are TRUE simultaneously.
"""

import logging
from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np

from re_storage.core.exceptions import SoCBoundsError
from re_storage.core.types import (
    ChargingMode,
    EnergyKWH,
    GridChargeMode,
    PowerKW,
    Ratio,
    StrategyMode,
    TimePeriod,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


class BatteryState(NamedTuple):
    """
    Immutable snapshot of battery state at a single timestep.

    This is the output of a single dispatch step, capturing all
    relevant power flows and the resulting state of charge.

    Attributes:
        soc_kwh: State of charge at end of timestep (kWh).
        pv_charged_kw: Power from PV to battery (kW).
        grid_charged_kw: Power from grid to battery (kW).
        discharged_kw: Power from battery to load/grid (kW).
        discharge_permitted: Whether discharge was allowed this step.
        active_discharge_conditions: List of conditions that permitted discharge.
    """

    soc_kwh: EnergyKWH
    pv_charged_kw: PowerKW
    grid_charged_kw: PowerKW
    discharged_kw: PowerKW
    discharge_permitted: bool
    active_discharge_conditions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatteryConfig:
    """
    Immutable battery system configuration.

    Contains all parameters needed for dispatch decisions.
    Frozen to prevent accidental mutation during simulation.

    Attributes:
        usable_capacity_kwh: Net usable battery capacity (kWh).
        power_rating_kw: Maximum charge/discharge power (kW).
        charge_efficiency: Charging efficiency (0-1 ratio).
        discharge_efficiency: Discharging efficiency (0-1 ratio).
        strategy_mode: Arbitrage or peak shaving.
        charging_mode: Time window or precharge target.
        charge_start_hour: Start of charging window (0-23).
        charge_end_hour: End of charging window (0-23).
        precharge_target_hour: Hour to reach target SoC.
        precharge_target_soc_kwh: Target SoC for precharge mode.
        min_direct_pv_share: Minimum PV that must serve load (0-1).
        active_pv2bess_share: Maximum PV share to divert to battery (0-1).
        demand_target_kw: Peak shaving demand target (kW).
        grid_charge_mode: Whether grid charging is allowed.
        grid_charge_capacity_kw: Max grid charging power (kW).
    """

    usable_capacity_kwh: EnergyKWH
    power_rating_kw: PowerKW
    charge_efficiency: Ratio
    discharge_efficiency: Ratio
    strategy_mode: StrategyMode
    charging_mode: ChargingMode
    charge_start_hour: int
    charge_end_hour: int
    precharge_target_hour: int
    precharge_target_soc_kwh: EnergyKWH
    min_direct_pv_share: Ratio
    active_pv2bess_share: Ratio
    demand_target_kw: PowerKW
    grid_charge_mode: GridChargeMode
    grid_charge_capacity_kw: PowerKW

    # Discharge condition flags (for arbitrage mode)
    when_needed: bool = True
    after_sunset: bool = False
    optimize_mode: bool = False
    peak_mode: bool = True

    # Optimization windows (Vietnam defaults)
    optimize_start_hour: int = 16
    optimize_end_hour: int = 21
    sunday_peak_start_hour: int = 17
    sunday_peak_end_hour: int = 20

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.usable_capacity_kwh <= 0:
            raise ValueError(f"usable_capacity_kwh must be positive: {self.usable_capacity_kwh}")
        if self.power_rating_kw <= 0:
            raise ValueError(f"power_rating_kw must be positive: {self.power_rating_kw}")
        if not 0 < self.charge_efficiency <= 1:
            raise ValueError(f"charge_efficiency must be in (0, 1]: {self.charge_efficiency}")
        if not 0 < self.discharge_efficiency <= 1:
            raise ValueError(
                f"discharge_efficiency must be in (0, 1]: {self.discharge_efficiency}"
            )


@dataclass(frozen=True)
class DischargeConditions:
    """
    Flags indicating which discharge conditions are currently active.

    Used to track and log when multiple overlapping conditions permit
    discharge, which can lead to unexpected behavior.

    Reference: model_architecture.md Risk 1 (Discharge Strategy Complexity)
    """

    when_needed: bool = False
    after_sunset: bool = False
    optimize: bool = False
    peak: bool = False

    def any_active(self) -> bool:
        """Return True if any discharge condition is active."""
        return self.when_needed or self.after_sunset or self.optimize or self.peak

    def active_list(self) -> list[str]:
        """Return list of active condition names."""
        active = []
        if self.when_needed:
            active.append("when_needed")
        if self.after_sunset:
            active.append("after_sunset")
        if self.optimize:
            active.append("optimize")
        if self.peak:
            active.append("peak")
        return active

    def count_active(self) -> int:
        """Return number of active conditions."""
        return sum([self.when_needed, self.after_sunset, self.optimize, self.peak])


# =============================================================================
# CHARGE CALCULATIONS
# =============================================================================


def calculate_charge_limit(
    current_soc_kwh: EnergyKWH,
    max_capacity_kwh: EnergyKWH,
    charge_efficiency: Ratio,
    step_hours: float = 1.0,
) -> PowerKW:
    """
    Calculate maximum power that can be accepted for charging.

    The charge limit is constrained by:
    1. Available headroom in battery (capacity - current SoC)
    2. Efficiency losses (more input power needed per kWh stored)

    Formula:
        ChargeLimit_kWh = (MaxCapacity - CurrentSoC) / ChargeEfficiency
        ChargeLimit_kW = ChargeLimit_kWh / StepHours

    Args:
        current_soc_kwh: Current state of charge (kWh).
        max_capacity_kwh: Maximum usable capacity (kWh).
        charge_efficiency: Charging efficiency (0-1).
            E.g., 0.9 means 10% of input energy is lost as heat.
        step_hours: Timestep duration in hours. Default 1.0.

    Returns:
        Maximum charging power that can be accepted (kW).

    Example:
        >>> calculate_charge_limit(
        ...     current_soc_kwh=60.0,
        ...     max_capacity_kwh=100.0,
        ...     charge_efficiency=0.9,
        ... )
        44.44...  # (100-60)/0.9 = 44.44 kW can be accepted
    """
    if current_soc_kwh < 0:
        raise ValueError(f"current_soc_kwh cannot be negative: {current_soc_kwh}")
    if max_capacity_kwh <= 0:
        raise ValueError(f"max_capacity_kwh must be positive: {max_capacity_kwh}")
    if not 0 < charge_efficiency <= 1:
        raise ValueError(f"charge_efficiency must be in (0, 1]: {charge_efficiency}")
    if step_hours <= 0:
        raise ValueError(f"step_hours must be positive: {step_hours}")

    available_capacity_kwh = max(max_capacity_kwh - current_soc_kwh, 0.0)
    charge_limit_kwh = available_capacity_kwh / charge_efficiency
    charge_limit_kw = charge_limit_kwh / step_hours

    return charge_limit_kw


def calculate_pv_to_bess(
    solar_gen_kw: PowerKW,
    load_kw: PowerKW,
    current_soc_kwh: EnergyKWH,
    hour: int,
    config: BatteryConfig,
    is_peak_period: bool,
    step_hours: float = 1.0,
) -> PowerKW:
    """
    Calculate power to divert from PV to battery charging.

    Implements two charging modes:
    1. TIME_WINDOW: Charge during specific hours (e.g., 9am-3pm)
    2. PRECHARGE_TARGET: Charge to reach target SoC by specific hour

    Constraints applied:
    - Minimum direct PV share to load (Min_DirectPVShare)
    - Available charge capacity (ChargeLimit)
    - Inverter power rating

    Reference: model_architecture.md §A.2

    Args:
        solar_gen_kw: Current solar generation (kW).
        load_kw: Current site load (kW).
        current_soc_kwh: Current battery SoC (kWh).
        hour: Hour of day (0-23).
        config: Battery configuration.
        is_peak_period: Whether current timestep is peak tariff period.
        step_hours: Timestep duration in hours.

    Returns:
        Power to divert from PV to battery (kW).

    Note:
        In TIME_WINDOW mode, battery does NOT charge during peak periods
        to preserve capacity for arbitrage discharge.
    """
    if solar_gen_kw <= 0:
        return 0.0

    # Calculate charge capacity limit
    charge_limit_kw = calculate_charge_limit(
        current_soc_kwh=current_soc_kwh,
        max_capacity_kwh=config.usable_capacity_kwh,
        charge_efficiency=config.charge_efficiency,
        step_hours=step_hours,
    )

    # Also respect inverter rating
    max_charge_power = min(charge_limit_kw, config.power_rating_kw)

    if max_charge_power <= 0:
        return 0.0  # Battery is full

    # Calculate minimum PV that must serve load
    min_pv_to_load = load_kw * config.min_direct_pv_share
    available_for_charging = max(solar_gen_kw - min_pv_to_load, 0.0)

    if available_for_charging <= 0:
        return 0.0

    if config.charging_mode == ChargingMode.TIME_WINDOW:
        return _calculate_pv_to_bess_time_window(
            available_for_charging=available_for_charging,
            max_charge_power=max_charge_power,
            hour=hour,
            config=config,
            is_peak_period=is_peak_period,
        )

    elif config.charging_mode == ChargingMode.PRECHARGE_TARGET:
        return _calculate_pv_to_bess_precharge(
            available_for_charging=available_for_charging,
            max_charge_power=max_charge_power,
            current_soc_kwh=current_soc_kwh,
            hour=hour,
            config=config,
            step_hours=step_hours,
        )

    else:
        raise ValueError(f"Unknown charging mode: {config.charging_mode}")


def _calculate_pv_to_bess_time_window(
    available_for_charging: PowerKW,
    max_charge_power: PowerKW,
    hour: int,
    config: BatteryConfig,
    is_peak_period: bool,
) -> PowerKW:
    """
    Time window charging: charge during specific hours, not during peak.

    Reference: model_architecture.md §A.2 Mode 1
    """
    # Check if within charging window
    if config.charge_start_hour <= config.charge_end_hour:
        in_window = config.charge_start_hour <= hour <= config.charge_end_hour
    else:
        # Window wraps midnight (e.g., 22:00 to 06:00)
        in_window = hour >= config.charge_start_hour or hour <= config.charge_end_hour

    if not in_window:
        return 0.0

    # Do not charge during peak periods (preserve for arbitrage)
    if is_peak_period:
        return 0.0

    # Apply share limit and capacity constraint
    desired_charge = available_for_charging * config.active_pv2bess_share
    return min(desired_charge, max_charge_power)


def _calculate_pv_to_bess_precharge(
    available_for_charging: PowerKW,
    max_charge_power: PowerKW,
    current_soc_kwh: EnergyKWH,
    hour: int,
    config: BatteryConfig,
    step_hours: float,
) -> PowerKW:
    """
    Precharge target: charge to reach target SoC by specific hour.

    Reference: model_architecture.md §A.2 Mode 2
    """
    # Only charge before target hour
    if hour >= config.precharge_target_hour:
        return 0.0

    # Calculate required charge rate to reach target
    soc_deficit_kwh = max(config.precharge_target_soc_kwh - current_soc_kwh, 0.0)

    if soc_deficit_kwh <= 0:
        return 0.0  # Already at or above target

    hours_remaining = config.precharge_target_hour - hour
    if hours_remaining <= 0:
        hours_remaining = 1  # Avoid division by zero

    # Required charge rate (accounting for efficiency)
    required_charge_kw = soc_deficit_kwh / (config.charge_efficiency * hours_remaining)

    # Constrain by available power and limits
    return min(required_charge_kw, available_for_charging, max_charge_power)


# =============================================================================
# DISCHARGE PERMISSION LOGIC
# =============================================================================


def evaluate_discharge_permission(
    hour: int,
    load_kw: PowerKW,
    solar_gen_kw: PowerKW,
    grid_load_after_solar_kw: PowerKW,
    config: BatteryConfig,
    is_peak_period: bool,
    is_sunday: bool = False,
) -> DischargeConditions:
    """
    Evaluate which discharge conditions are active.

    This implements the complex 4-condition OR logic from Calc!Col J.
    Returns a DischargeConditions object showing which conditions fired.

    WARNING (Risk 1): Conditions are evaluated with OR logic, meaning ANY
    single TRUE condition enables discharge. This can cause unexpected
    discharge during off-peak periods if flags overlap. We log when
    multiple conditions are TRUE simultaneously.

    Reference: model_architecture.md §A.3

    Args:
        hour: Hour of day (0-23).
        load_kw: Current site load (kW).
        solar_gen_kw: Current solar generation (kW).
        grid_load_after_solar_kw: Net grid load after solar (kW).
        config: Battery configuration with strategy mode and flags.
        is_peak_period: Whether current timestep is peak tariff period.
        is_sunday: Whether current day is Sunday.

    Returns:
        DischargeConditions showing which conditions are active.
    """
    if config.strategy_mode == StrategyMode.PEAK_SHAVING:
        # Peak shaving: discharge only when exceeding demand target
        peak_shaving_needed = grid_load_after_solar_kw > config.demand_target_kw
        return DischargeConditions(when_needed=peak_shaving_needed)

    # Arbitrage mode: evaluate 4 conditions
    conditions = DischargeConditions(
        when_needed=config.when_needed and (load_kw > solar_gen_kw),
        after_sunset=config.after_sunset and (hour >= 17),
        optimize=config.optimize_mode
        and (
            (config.optimize_start_hour <= hour <= config.optimize_end_hour) or is_peak_period
        ),
        peak=config.peak_mode
        and (
            is_peak_period
            or (
                is_sunday
                and (config.sunday_peak_start_hour <= hour <= config.sunday_peak_end_hour)
            )
        ),
    )

    # Log warning if multiple conditions are active (potential strategy conflict)
    if conditions.count_active() > 1:
        logger.warning(
            f"Multiple discharge conditions active at hour {hour}: "
            f"{conditions.active_list()}. Review dispatch strategy for unintended overlap."
        )

    return conditions




# =============================================================================
# DISCHARGE CALCULATIONS
# =============================================================================


def calculate_discharge_power(
    load_kw: PowerKW,
    solar_gen_kw: PowerKW,
    pv_to_bess_kw: PowerKW,
    current_soc_kwh: EnergyKWH,
    config: BatteryConfig,
    discharge_permitted: bool,
    step_hours: float = 1.0,
) -> PowerKW:
    """
    Calculate actual discharge power for this timestep.

    Discharge is constrained by:
    1. Permission (from evaluate_discharge_permission)
    2. Available energy in battery (SoC)
    3. Inverter power rating
    4. Load requirement (don't discharge more than needed)

    Args:
        load_kw: Current site load (kW).
        solar_gen_kw: Current solar generation (kW).
        pv_to_bess_kw: Power being diverted to battery (kW).
        current_soc_kwh: Current battery SoC (kWh).
        config: Battery configuration.
        discharge_permitted: Whether discharge is allowed.
        step_hours: Timestep duration in hours.

    Returns:
        Discharge power (kW). Zero if discharge not permitted or not needed.
    """
    if not discharge_permitted:
        return 0.0

    if current_soc_kwh <= 0:
        return 0.0  # Nothing to discharge

    # Calculate unmet load after solar (and after PV diversion)
    pv_available_for_load = max(solar_gen_kw - pv_to_bess_kw, 0.0)
    unmet_load_kw = max(load_kw - pv_available_for_load, 0.0)

    if unmet_load_kw <= 0:
        return 0.0  # Load fully served by solar

    # Calculate maximum discharge based on SoC and efficiency
    # Discharge extracts energy, so we need to account for efficiency loss
    max_discharge_from_soc_kwh = current_soc_kwh * config.discharge_efficiency
    max_discharge_from_soc_kw = max_discharge_from_soc_kwh / step_hours

    # Constrain by inverter rating
    max_discharge_kw = min(max_discharge_from_soc_kw, config.power_rating_kw)

    # Don't discharge more than needed
    return min(unmet_load_kw, max_discharge_kw)


def calculate_grid_charge_power(
    current_soc_kwh: EnergyKWH,
    config: BatteryConfig,
    step_hours: float = 1.0,
    max_power_kw: PowerKW | None = None,
) -> PowerKW:
    """
    Calculate power to charge battery from grid.

    Grid charging is controlled by GridChargeMode:
    - DISABLED: No grid charging
    - TO_TARGET: Charge to CapGrid target
    - TO_FULL: Charge to full capacity

    Reference: model_architecture.md Risk 2 (Grid Charging Flag Ambiguity)

    Args:
        current_soc_kwh: Current battery SoC (kWh).
        config: Battery configuration.
        step_hours: Timestep duration in hours.
        max_power_kw: Optional override for maximum charging power.
            If None, uses config.power_rating_kw.

    Returns:
        Grid charging power (kW).
    """
    if config.grid_charge_mode == GridChargeMode.DISABLED:
        return 0.0

    # Determine target capacity based on mode
    if config.grid_charge_mode == GridChargeMode.TO_TARGET:
        target_kwh = config.grid_charge_capacity_kw  # CapGrid target
    elif config.grid_charge_mode == GridChargeMode.TO_FULL:
        target_kwh = config.usable_capacity_kwh
    else:
        return 0.0

    # Calculate charge needed
    charge_needed_kwh = max(target_kwh - current_soc_kwh, 0.0)

    if charge_needed_kwh <= 0:
        return 0.0

    # Calculate charge rate
    charge_rate_kw = charge_needed_kwh / (config.charge_efficiency * step_hours)

    # Determine power limit
    power_limit_kw = config.power_rating_kw
    if max_power_kw is not None:
        power_limit_kw = min(power_limit_kw, max_power_kw)

    # Constrain by grid charge capacity and power limit
    return min(charge_rate_kw, config.grid_charge_capacity_kw, power_limit_kw)


# =============================================================================
# STATE OF CHARGE UPDATE
# =============================================================================


def update_soc(
    previous_soc_kwh: EnergyKWH,
    pv_charged_kw: PowerKW,
    grid_charged_kw: PowerKW,
    discharged_kw: PowerKW,
    config: BatteryConfig,
    step_hours: float = 1.0,
    timestep: int | None = None,
) -> EnergyKWH:
    """
    Calculate new State of Charge after a timestep.

    Applies charging efficiency (loss during charge) and discharge
    efficiency (loss during discharge) to update SoC.

    Formula (from Calc!Col M, model_architecture.md §A.4):
        New_SoC = BOUNDED[0, Capacity](
            Previous_SoC
            + TotalCharged × Charge_Efficiency
            - Discharged / Discharge_Efficiency
        )

    Note on efficiency application:
    - Charging: We receive 'pv_charged_kw' as INPUT power, so we
      multiply by efficiency to get energy STORED.
    - Discharging: We deliver 'discharged_kw' as OUTPUT power, so we
      divide by efficiency to get energy EXTRACTED from battery.

    Args:
        previous_soc_kwh: SoC at start of timestep (kWh).
        pv_charged_kw: Power from PV to battery (kW).
        grid_charged_kw: Power from grid to battery (kW).
        discharged_kw: Power from battery to load (kW).
        config: Battery configuration with efficiencies.
        step_hours: Timestep duration in hours.
        timestep: Optional timestep index for error reporting.

    Returns:
        New SoC at end of timestep (kWh), bounded to [0, capacity].

    Raises:
        SoCBoundsError: If calculation results in physically impossible SoC.
            This indicates a bug in dispatch logic, not just floating point.
    """
    # Convert power to energy
    total_charged_kwh = (pv_charged_kw + grid_charged_kw) * step_hours
    discharged_kwh = discharged_kw * step_hours

    # Apply efficiencies
    energy_stored_kwh = total_charged_kwh * config.charge_efficiency
    energy_extracted_kwh = discharged_kwh / config.discharge_efficiency

    # Calculate new SoC (unbounded)
    new_soc_unbounded = previous_soc_kwh + energy_stored_kwh - energy_extracted_kwh

    # Check for significant bounds violation (indicates logic error)
    tolerance = 0.01  # 10 Wh tolerance for floating point

    if new_soc_unbounded < -tolerance:
        raise SoCBoundsError(
            f"SoC calculation resulted in negative value: {new_soc_unbounded:.4f} kWh. "
            f"Previous={previous_soc_kwh:.4f}, Stored={energy_stored_kwh:.4f}, "
            f"Extracted={energy_extracted_kwh:.4f}. "
            "This indicates dispatch logic allowed over-discharge.",
            soc_kwh=new_soc_unbounded,
            max_capacity_kwh=config.usable_capacity_kwh,
            timestep=timestep,
        )

    if new_soc_unbounded > config.usable_capacity_kwh + tolerance:
        raise SoCBoundsError(
            f"SoC calculation resulted in over-capacity: {new_soc_unbounded:.4f} kWh "
            f"(capacity: {config.usable_capacity_kwh:.4f} kWh). "
            f"Previous={previous_soc_kwh:.4f}, Stored={energy_stored_kwh:.4f}, "
            f"Extracted={energy_extracted_kwh:.4f}. "
            "This indicates dispatch logic allowed over-charge.",
            soc_kwh=new_soc_unbounded,
            max_capacity_kwh=config.usable_capacity_kwh,
            timestep=timestep,
        )

    # Apply bounds (for floating point tolerance only)
    new_soc = np.clip(new_soc_unbounded, 0.0, config.usable_capacity_kwh)

    return float(new_soc)


# =============================================================================
# SINGLE TIMESTEP DISPATCH
# =============================================================================


def dispatch_single_timestep(
    solar_gen_kw: PowerKW,
    load_kw: PowerKW,
    previous_soc_kwh: EnergyKWH,
    hour: int,
    config: BatteryConfig,
    is_peak_period: bool,
    is_sunday: bool = False,
    step_hours: float = 1.0,
    timestep: int | None = None,
) -> BatteryState:
    """
    Execute battery dispatch for a single timestep.

    This is the main entry point for the dispatch engine, orchestrating:
    1. PV-to-BESS charging decision
    2. Grid charging decision
    3. Discharge permission evaluation
    4. Discharge power calculation
    5. SoC update

    Args:
        solar_gen_kw: Solar generation this timestep (kW).
        load_kw: Site load this timestep (kW).
        previous_soc_kwh: SoC at start of timestep (kWh).
        hour: Hour of day (0-23).
        config: Battery configuration.
        is_peak_period: Whether this is a peak tariff period.
        is_sunday: Whether this is a Sunday.
        step_hours: Timestep duration in hours.
        timestep: Optional timestep index for logging/errors.

    Returns:
        BatteryState with all power flows and resulting SoC.
    """
    # Step 1: Calculate PV charging
    # PV charging has priority over grid charging
    pv_to_bess_kw = calculate_pv_to_bess(
        solar_gen_kw=solar_gen_kw,
        load_kw=load_kw,
        current_soc_kwh=previous_soc_kwh,
        hour=hour,
        config=config,
        is_peak_period=is_peak_period,
        step_hours=step_hours,
    )

    # Step 2: Calculate grid charging
    # Must respect remaining capacity and power after PV charging
    pv_charged_kwh = pv_to_bess_kw * step_hours * config.charge_efficiency
    soc_after_pv = min(previous_soc_kwh + pv_charged_kwh, config.usable_capacity_kwh)
    remaining_power_kw = max(config.power_rating_kw - pv_to_bess_kw, 0.0)

    grid_charge_kw = calculate_grid_charge_power(
        current_soc_kwh=soc_after_pv,
        config=config,
        step_hours=step_hours,
        max_power_kw=remaining_power_kw,
    )

    # Step 3: Calculate intermediate SoC after all charging
    # (needed to determine discharge capacity)
    total_charged_kwh = (pv_to_bess_kw + grid_charge_kw) * step_hours
    soc_after_charge = min(
        previous_soc_kwh + total_charged_kwh * config.charge_efficiency,
        config.usable_capacity_kwh,
    )

    # Step 4: Evaluate discharge permission
    grid_load_after_solar = max(load_kw - (solar_gen_kw - pv_to_bess_kw), 0.0)

    conditions = evaluate_discharge_permission(
        hour=hour,
        load_kw=load_kw,
        solar_gen_kw=solar_gen_kw,
        grid_load_after_solar_kw=grid_load_after_solar,
        config=config,
        is_peak_period=is_peak_period,
        is_sunday=is_sunday,
    )

    # Step 5: Calculate discharge power
    discharge_kw = calculate_discharge_power(
        load_kw=load_kw,
        solar_gen_kw=solar_gen_kw,
        pv_to_bess_kw=pv_to_bess_kw,
        current_soc_kwh=soc_after_charge,  # Use SoC after charging
        config=config,
        discharge_permitted=conditions.any_active(),
        step_hours=step_hours,
    )

    # Step 6: Update final SoC
    final_soc = update_soc(
        previous_soc_kwh=previous_soc_kwh,
        pv_charged_kw=pv_to_bess_kw,
        grid_charged_kw=grid_charge_kw,
        discharged_kw=discharge_kw,
        config=config,
        step_hours=step_hours,
        timestep=timestep,
    )

    return BatteryState(
        soc_kwh=final_soc,
        pv_charged_kw=pv_to_bess_kw,
        grid_charged_kw=grid_charge_kw,
        discharged_kw=discharge_kw,
        discharge_permitted=conditions.any_active(),
        active_discharge_conditions=conditions.active_list(),
    )
