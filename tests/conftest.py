"""
Pytest configuration and shared fixtures.

This module provides reusable test fixtures for the RE-Storage test suite.
Fixtures follow the "Arrange-Act-Assert" pattern and provide common
test data configurations.
"""

import pytest

from re_storage.core.types import ChargingMode, GridChargeMode, StrategyMode
from re_storage.physics.battery import BatteryConfig


@pytest.fixture
def default_battery_config() -> BatteryConfig:
    """
    Standard battery configuration for unit tests.

    Represents a typical 100 kWh / 50 kW battery system with
    90% round-trip efficiency (charge and discharge).
    """
    return BatteryConfig(
        usable_capacity_kwh=100.0,
        power_rating_kw=50.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=StrategyMode.ARBITRAGE,
        charging_mode=ChargingMode.TIME_WINDOW,
        charge_start_hour=9,
        charge_end_hour=15,
        precharge_target_hour=17,
        precharge_target_soc_kwh=80.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_target_kw=100.0,
        grid_charge_mode=GridChargeMode.DISABLED,
        grid_charge_capacity_kw=0.0,
        when_needed=True,
        after_sunset=False,
        optimize_mode=False,
        peak_mode=True,
    )


@pytest.fixture
def peak_shaving_config() -> BatteryConfig:
    """
    Battery configuration for peak shaving mode tests.
    """
    return BatteryConfig(
        usable_capacity_kwh=100.0,
        power_rating_kw=50.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=StrategyMode.PEAK_SHAVING,
        charging_mode=ChargingMode.TIME_WINDOW,
        charge_start_hour=9,
        charge_end_hour=15,
        precharge_target_hour=17,
        precharge_target_soc_kwh=80.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_target_kw=80.0,  # Demand target for peak shaving
        grid_charge_mode=GridChargeMode.DISABLED,
        grid_charge_capacity_kw=0.0,
    )


@pytest.fixture
def precharge_config() -> BatteryConfig:
    """
    Battery configuration for precharge target mode tests.
    """
    return BatteryConfig(
        usable_capacity_kwh=100.0,
        power_rating_kw=50.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=StrategyMode.ARBITRAGE,
        charging_mode=ChargingMode.PRECHARGE_TARGET,
        charge_start_hour=9,
        charge_end_hour=15,
        precharge_target_hour=17,
        precharge_target_soc_kwh=80.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_target_kw=100.0,
        grid_charge_mode=GridChargeMode.DISABLED,
        grid_charge_capacity_kw=0.0,
    )


@pytest.fixture
def full_soc_config() -> BatteryConfig:
    """
    Configuration representing a fully charged battery.
    
    Useful for testing discharge-only scenarios.
    """
    return BatteryConfig(
        usable_capacity_kwh=100.0,
        power_rating_kw=50.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        strategy_mode=StrategyMode.ARBITRAGE,
        charging_mode=ChargingMode.TIME_WINDOW,
        charge_start_hour=9,
        charge_end_hour=15,
        precharge_target_hour=17,
        precharge_target_soc_kwh=80.0,
        min_direct_pv_share=0.0,
        active_pv2bess_share=1.0,
        demand_target_kw=100.0,
        grid_charge_mode=GridChargeMode.DISABLED,
        grid_charge_capacity_kw=0.0,
        when_needed=True,
        after_sunset=True,
        optimize_mode=False,
        peak_mode=True,
    )
