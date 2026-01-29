"""
Pydantic schemas for RE-Storage inputs.

These models provide strict validation for scalar inputs and single-row
structures before data enters the physics engine.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemAssumptions(BaseModel):
    """
    Global system parameters from the Assumption sheet.

    These values configure the physics engine and settlement logic.
    """

    model_config = ConfigDict(extra="forbid")

    # Capacity
    simulation_capacity_kwp: float = Field(gt=0, description="PVsyst model capacity")
    actual_capacity_kwp: float = Field(gt=0, description="Installed capacity")
    usable_bess_capacity_kwh: float = Field(ge=0, description="Net battery capacity")
    bess_power_rating_kw: float = Field(ge=0, description="Battery power limit")

    # Efficiency
    charge_efficiency: float = Field(ge=0.5, le=1.0)
    discharge_efficiency: float = Field(ge=0.5, le=1.0)

    # Strategy
    strategy_mode: int = Field(ge=1, le=2, description="1=Arbitrage, 2=Peak Shaving")
    charging_mode: int = Field(ge=1, le=2, description="1=Time Window, 2=Precharge")

    # Time windows
    charge_start_hour: int = Field(ge=0, le=23)
    charge_end_hour: int = Field(ge=0, le=23)
    precharge_target_hour: int = Field(ge=0, le=23)
    precharge_target_soc_kwh: float = Field(ge=0)

    # Constraints
    min_direct_pv_share: float = Field(ge=0, le=1.0, description="Min PV to load")
    active_pv2bess_share: float = Field(ge=0, le=1.0, description="Max PV to battery")
    demand_reduction_target: float = Field(ge=0, le=1.0)

    # DPPA
    strike_price_usd_per_kwh: float = Field(ge=0)
    k_factor: float = Field(gt=0, description="Loss adjustment factor")
    kpp: float = Field(gt=0, description="Price adjustment coefficient")

    # Toggles
    bess_enabled: bool
    dppa_enabled: bool

    @property
    def scale_factor(self) -> float:
        """Output scale factor to convert simulation to actual capacity."""
        return self.actual_capacity_kwp / self.simulation_capacity_kwp


class HourlyInputRow(BaseModel):
    """
    Single row of hourly time series data.

    Represents one timestep from the Data Input sheet.
    """

    model_config = ConfigDict(extra="forbid")

    datetime: datetime
    simulation_profile_kw: float = Field(ge=0)
    irradiation_wh_m2: float = Field(ge=0)
    load_kw: float = Field(ge=0)
    fmp_usd_per_kwh: float
    cfmp_usd_per_kwh: float


class DegradationRow(BaseModel):
    """
    Annual degradation factors from the Loss sheet.
    """

    model_config = ConfigDict(extra="forbid")

    year: int = Field(ge=1, le=30)
    pv_factor: float = Field(gt=0, le=1.0, description="PV output multiplier")
    battery_factor_no_replacement: float = Field(gt=0, le=1.0)
    battery_factor_with_replacement: float = Field(gt=0, le=1.0)
