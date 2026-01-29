"""
Unit tests for physics.battery module.

Tests cover:
1. Charge limit calculations
2. PV-to-BESS charging logic (both modes)
3. Discharge permission logic (all 4 conditions)
4. Discharge power calculations
5. SoC update with efficiency
6. Single timestep dispatch integration

Reference: AGENTS.md §4 (Testing Requirements)
"""

import pytest
from hypothesis import given, strategies as st, assume

from re_storage.core.exceptions import SoCBoundsError
from re_storage.core.types import ChargingMode, GridChargeMode, StrategyMode
from re_storage.physics.battery import (
    BatteryConfig,
    BatteryState,
    DischargeConditions,
    calculate_charge_limit,
    calculate_discharge_power,
    calculate_grid_charge_power,
    calculate_pv_to_bess,
    dispatch_single_timestep,
    evaluate_discharge_permission,
    update_soc,
)


# =============================================================================
# CHARGE LIMIT TESTS
# =============================================================================


class TestCalculateChargeLimit:
    """Tests for calculate_charge_limit function."""

    def test_empty_battery_full_capacity_available(self) -> None:
        """Empty battery should accept charge up to full capacity (adjusted for efficiency)."""
        result = calculate_charge_limit(
            current_soc_kwh=0.0,
            max_capacity_kwh=100.0,
            charge_efficiency=0.9,
            step_hours=1.0,
        )
        # 100 kWh / 0.9 efficiency = 111.11 kW can be accepted
        assert abs(result - 111.11) < 0.01

    def test_full_battery_zero_capacity(self) -> None:
        """Full battery should accept zero charge."""
        result = calculate_charge_limit(
            current_soc_kwh=100.0,
            max_capacity_kwh=100.0,
            charge_efficiency=0.9,
            step_hours=1.0,
        )
        assert result == 0.0

    def test_half_full_battery(self) -> None:
        """Half-full battery should accept half capacity."""
        result = calculate_charge_limit(
            current_soc_kwh=50.0,
            max_capacity_kwh=100.0,
            charge_efficiency=0.9,
            step_hours=1.0,
        )
        # 50 kWh / 0.9 = 55.56 kW
        assert abs(result - 55.56) < 0.01

    def test_step_hours_scaling(self) -> None:
        """Charge limit should scale inversely with step hours."""
        result_1hr = calculate_charge_limit(
            current_soc_kwh=0.0,
            max_capacity_kwh=100.0,
            charge_efficiency=1.0,
            step_hours=1.0,
        )
        result_half_hr = calculate_charge_limit(
            current_soc_kwh=0.0,
            max_capacity_kwh=100.0,
            charge_efficiency=1.0,
            step_hours=0.5,
        )
        # Half hour step means double the power for same energy
        assert result_half_hr == result_1hr * 2

    def test_negative_soc_raises(self) -> None:
        """Negative SoC should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_charge_limit(
                current_soc_kwh=-10.0,
                max_capacity_kwh=100.0,
                charge_efficiency=0.9,
            )

    def test_zero_capacity_raises(self) -> None:
        """Zero capacity should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_charge_limit(
                current_soc_kwh=0.0,
                max_capacity_kwh=0.0,
                charge_efficiency=0.9,
            )

    def test_invalid_efficiency_raises(self) -> None:
        """Efficiency outside (0, 1] should raise ValueError."""
        with pytest.raises(ValueError, match="charge_efficiency"):
            calculate_charge_limit(
                current_soc_kwh=0.0,
                max_capacity_kwh=100.0,
                charge_efficiency=1.5,
            )

    @given(
        soc=st.floats(min_value=0, max_value=100),
        capacity=st.floats(min_value=1, max_value=1000),
        efficiency=st.floats(min_value=0.5, max_value=1.0),
    )
    def test_charge_limit_always_non_negative(
        self, soc: float, capacity: float, efficiency: float
    ) -> None:
        """Property: Charge limit should always be >= 0."""
        assume(soc <= capacity)  # Valid SoC
        result = calculate_charge_limit(
            current_soc_kwh=soc,
            max_capacity_kwh=capacity,
            charge_efficiency=efficiency,
        )
        assert result >= 0


# =============================================================================
# PV TO BESS CHARGING TESTS
# =============================================================================


class TestCalculatePvToBess:
    """Tests for calculate_pv_to_bess function."""

    def test_no_solar_no_charging(self, default_battery_config: BatteryConfig) -> None:
        """No solar generation means no PV charging."""
        result = calculate_pv_to_bess(
            solar_gen_kw=0.0,
            load_kw=50.0,
            current_soc_kwh=0.0,
            hour=12,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert result == 0.0

    def test_full_battery_no_charging(self, default_battery_config: BatteryConfig) -> None:
        """Full battery should not accept charging."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=50.0,
            current_soc_kwh=100.0,  # Full
            hour=12,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert result == 0.0

    def test_time_window_inside_charges(self, default_battery_config: BatteryConfig) -> None:
        """Inside charging window should allow charging."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=12,  # Within 9-15 window
            config=default_battery_config,
            is_peak_period=False,
        )
        assert result > 0

    def test_time_window_outside_no_charge(self, default_battery_config: BatteryConfig) -> None:
        """Outside charging window should not charge."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=20,  # Outside 9-15 window
            config=default_battery_config,
            is_peak_period=False,
        )
        assert result == 0.0

    def test_peak_period_no_charge_time_window(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Peak period should prevent charging in time window mode."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=12,
            config=default_battery_config,
            is_peak_period=True,  # Peak period
        )
        assert result == 0.0

    def test_precharge_mode_before_target(self, precharge_config: BatteryConfig) -> None:
        """Precharge mode should charge before target hour."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=10,  # Before target hour 17
            config=precharge_config,
            is_peak_period=False,
        )
        assert result > 0

    def test_precharge_mode_after_target_no_charge(
        self, precharge_config: BatteryConfig
    ) -> None:
        """Precharge mode should not charge after target hour."""
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=18,  # After target hour 17
            config=precharge_config,
            is_peak_period=False,
        )
        assert result == 0.0

    def test_min_direct_pv_share_constraint(self) -> None:
        """Min direct PV share should limit charging."""
        config = BatteryConfig(
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
            min_direct_pv_share=0.5,  # 50% must go to load
            active_pv2bess_share=1.0,
            demand_target_kw=100.0,
            grid_charge_mode=GridChargeMode.DISABLED,
            grid_charge_capacity_kw=0.0,
        )
        result = calculate_pv_to_bess(
            solar_gen_kw=100.0,
            load_kw=80.0,  # 50% = 40 kW must serve load
            current_soc_kwh=0.0,
            hour=12,
            config=config,
            is_peak_period=False,
        )
        # 100 - 40 = 60 kW available for charging
        assert result <= 60.0

    def test_inverter_rating_constraint(self, default_battery_config: BatteryConfig) -> None:
        """Charging should be limited by inverter rating."""
        result = calculate_pv_to_bess(
            solar_gen_kw=200.0,  # More than inverter rating
            load_kw=0.0,
            current_soc_kwh=0.0,
            hour=12,
            config=default_battery_config,  # 50 kW rating
            is_peak_period=False,
        )
        assert result <= 50.0


# =============================================================================
# DISCHARGE PERMISSION TESTS
# =============================================================================


class TestEvaluateDischargePermission:
    """Tests for evaluate_discharge_permission function."""

    def test_peak_shaving_above_target_permits(
        self, peak_shaving_config: BatteryConfig
    ) -> None:
        """Peak shaving should permit discharge when load exceeds target."""
        conditions = evaluate_discharge_permission(
            hour=14,
            load_kw=100.0,
            solar_gen_kw=0.0,
            grid_load_after_solar_kw=100.0,  # Above 80 kW target
            config=peak_shaving_config,
            is_peak_period=False,
        )
        assert conditions.any_active()
        assert conditions.when_needed

    def test_peak_shaving_below_target_denies(
        self, peak_shaving_config: BatteryConfig
    ) -> None:
        """Peak shaving should deny discharge when load below target."""
        conditions = evaluate_discharge_permission(
            hour=14,
            load_kw=50.0,
            solar_gen_kw=0.0,
            grid_load_after_solar_kw=50.0,  # Below 80 kW target
            config=peak_shaving_config,
            is_peak_period=False,
        )
        assert not conditions.any_active()

    def test_arbitrage_when_needed_permits(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """When_needed should permit when load > solar."""
        conditions = evaluate_discharge_permission(
            hour=14,
            load_kw=100.0,
            solar_gen_kw=50.0,  # Load > Solar
            grid_load_after_solar_kw=50.0,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert conditions.when_needed
        assert conditions.any_active()

    def test_arbitrage_when_needed_denies(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """When_needed should deny when solar > load."""
        conditions = evaluate_discharge_permission(
            hour=14,
            load_kw=50.0,
            solar_gen_kw=100.0,  # Solar > Load
            grid_load_after_solar_kw=0.0,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert not conditions.when_needed

    def test_after_sunset_permits_after_5pm(
        self, full_soc_config: BatteryConfig
    ) -> None:
        """After_sunset should permit discharge after 17:00."""
        conditions = evaluate_discharge_permission(
            hour=18,  # After 17:00
            load_kw=50.0,
            solar_gen_kw=100.0,
            grid_load_after_solar_kw=0.0,
            config=full_soc_config,
            is_peak_period=False,
        )
        assert conditions.after_sunset

    def test_after_sunset_denies_before_5pm(
        self, full_soc_config: BatteryConfig
    ) -> None:
        """After_sunset should deny discharge before 17:00."""
        conditions = evaluate_discharge_permission(
            hour=14,  # Before 17:00
            load_kw=50.0,
            solar_gen_kw=100.0,
            grid_load_after_solar_kw=0.0,
            config=full_soc_config,
            is_peak_period=False,
        )
        assert not conditions.after_sunset

    def test_peak_mode_permits_during_peak(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Peak mode should permit during peak period."""
        conditions = evaluate_discharge_permission(
            hour=14,
            load_kw=50.0,
            solar_gen_kw=100.0,
            grid_load_after_solar_kw=0.0,
            config=default_battery_config,
            is_peak_period=True,  # Peak period
        )
        assert conditions.peak

    def test_peak_mode_sunday_window(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Peak mode should permit during Sunday peak window."""
        conditions = evaluate_discharge_permission(
            hour=18,  # Sunday peak window (17-20)
            load_kw=50.0,
            solar_gen_kw=100.0,
            grid_load_after_solar_kw=0.0,
            config=default_battery_config,
            is_peak_period=False,
            is_sunday=True,
        )
        assert conditions.peak

    def test_multiple_conditions_logs_warning(
        self, full_soc_config: BatteryConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Multiple active conditions should log a warning."""
        import logging

        caplog.set_level(logging.WARNING)

        # Create conditions where multiple are true
        conditions = evaluate_discharge_permission(
            hour=18,  # After sunset + peak on Sunday
            load_kw=100.0,
            solar_gen_kw=50.0,  # Load > Solar (when_needed)
            grid_load_after_solar_kw=50.0,
            config=full_soc_config,
            is_peak_period=True,
            is_sunday=True,
        )

        assert conditions.count_active() > 1
        assert "Multiple discharge conditions" in caplog.text


# =============================================================================
# DISCHARGE POWER TESTS
# =============================================================================


class TestCalculateDischargePower:
    """Tests for calculate_discharge_power function."""

    def test_no_permission_no_discharge(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """No discharge permission means zero discharge."""
        result = calculate_discharge_power(
            load_kw=100.0,
            solar_gen_kw=0.0,
            pv_to_bess_kw=0.0,
            current_soc_kwh=100.0,
            config=default_battery_config,
            discharge_permitted=False,
        )
        assert result == 0.0

    def test_empty_battery_no_discharge(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Empty battery cannot discharge."""
        result = calculate_discharge_power(
            load_kw=100.0,
            solar_gen_kw=0.0,
            pv_to_bess_kw=0.0,
            current_soc_kwh=0.0,  # Empty
            config=default_battery_config,
            discharge_permitted=True,
        )
        assert result == 0.0

    def test_solar_meets_load_no_discharge(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """If solar meets load, no discharge needed."""
        result = calculate_discharge_power(
            load_kw=50.0,
            solar_gen_kw=100.0,  # More than load
            pv_to_bess_kw=0.0,
            current_soc_kwh=100.0,
            config=default_battery_config,
            discharge_permitted=True,
        )
        assert result == 0.0

    def test_discharge_limited_by_unmet_load(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Discharge should not exceed unmet load."""
        result = calculate_discharge_power(
            load_kw=30.0,
            solar_gen_kw=10.0,
            pv_to_bess_kw=0.0,
            current_soc_kwh=100.0,
            config=default_battery_config,
            discharge_permitted=True,
        )
        # Unmet load = 30 - 10 = 20 kW
        assert result == 20.0

    def test_discharge_limited_by_inverter_rating(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Discharge should not exceed inverter rating."""
        result = calculate_discharge_power(
            load_kw=200.0,  # More than inverter can handle
            solar_gen_kw=0.0,
            pv_to_bess_kw=0.0,
            current_soc_kwh=100.0,
            config=default_battery_config,  # 50 kW rating
            discharge_permitted=True,
        )
        assert result <= 50.0

    def test_discharge_limited_by_soc(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Discharge should be limited by available SoC."""
        result = calculate_discharge_power(
            load_kw=100.0,
            solar_gen_kw=0.0,
            pv_to_bess_kw=0.0,
            current_soc_kwh=10.0,  # Only 10 kWh available
            config=default_battery_config,
            discharge_permitted=True,
        )
        # Max discharge from 10 kWh at 95% eff = 9.5 kW for 1 hour
        assert result <= 10.0


# =============================================================================
# SOC UPDATE TESTS
# =============================================================================


class TestUpdateSoc:
    """Tests for update_soc function."""

    def test_charge_increases_soc(self, default_battery_config: BatteryConfig) -> None:
        """Charging should increase SoC."""
        result = update_soc(
            previous_soc_kwh=50.0,
            pv_charged_kw=10.0,
            grid_charged_kw=0.0,
            discharged_kw=0.0,
            config=default_battery_config,
        )
        # 10 kW * 1 hr * 0.95 eff = 9.5 kWh stored
        assert result == pytest.approx(59.5, abs=0.01)

    def test_discharge_decreases_soc(self, default_battery_config: BatteryConfig) -> None:
        """Discharging should decrease SoC."""
        result = update_soc(
            previous_soc_kwh=50.0,
            pv_charged_kw=0.0,
            grid_charged_kw=0.0,
            discharged_kw=10.0,
            config=default_battery_config,
        )
        # 10 kW output / 0.95 eff = 10.53 kWh extracted
        assert result < 50.0
        assert result == pytest.approx(39.47, abs=0.01)

    def test_charge_and_discharge_net(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Simultaneous charge and discharge should net correctly."""
        result = update_soc(
            previous_soc_kwh=50.0,
            pv_charged_kw=20.0,  # +19 kWh stored
            grid_charged_kw=0.0,
            discharged_kw=10.0,  # -10.53 kWh extracted
            config=default_battery_config,
        )
        # Net: 50 + 19 - 10.53 ≈ 58.47
        assert result > 50.0

    def test_soc_clamped_at_max_small_overshoot(self, default_battery_config: BatteryConfig) -> None:
        """Small SoC overshoot (within tolerance of 0.01 kWh) should be clamped."""
        # Charge that results in just slightly over capacity (within 0.01 tolerance)
        result = update_soc(
            previous_soc_kwh=99.99,
            pv_charged_kw=0.015,  # Would add ~0.014 kWh, total ~100.004
            grid_charged_kw=0.0,
            discharged_kw=0.0,
            config=default_battery_config,
        )
        # Small overshoot within tolerance should clamp to 100
        assert result == 100.0

    def test_significant_overcharge_raises(self, default_battery_config: BatteryConfig) -> None:
        """Significant overcharge should raise SoCBoundsError (fail loudly)."""
        # This tests the "fail loudly" philosophy from AGENTS.md
        with pytest.raises(SoCBoundsError, match="over-capacity"):
            update_soc(
                previous_soc_kwh=95.0,
                pv_charged_kw=50.0,  # Would add 47.5 kWh = 142.5 total
                grid_charged_kw=0.0,
                discharged_kw=0.0,
                config=default_battery_config,
            )

    def test_soc_clamped_at_zero(self, default_battery_config: BatteryConfig) -> None:
        """SoC should be clamped at zero (within tolerance)."""
        result = update_soc(
            previous_soc_kwh=5.0,
            pv_charged_kw=0.0,
            grid_charged_kw=0.0,
            discharged_kw=4.5,  # Would extract ~4.74 kWh
            config=default_battery_config,
        )
        assert result >= 0.0

    def test_significant_underflow_raises(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Significant SoC underflow should raise SoCBoundsError."""
        with pytest.raises(SoCBoundsError, match="negative"):
            update_soc(
                previous_soc_kwh=5.0,
                pv_charged_kw=0.0,
                grid_charged_kw=0.0,
                discharged_kw=50.0,  # Way more than available
                config=default_battery_config,
            )

    def test_significant_overflow_raises(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Significant SoC overflow should raise SoCBoundsError."""
        with pytest.raises(SoCBoundsError, match="over-capacity"):
            update_soc(
                previous_soc_kwh=95.0,
                pv_charged_kw=100.0,  # Would add 95 kWh
                grid_charged_kw=0.0,
                discharged_kw=0.0,
                config=default_battery_config,
            )

    @given(
        soc=st.floats(min_value=0, max_value=100),
        charge=st.floats(min_value=0, max_value=10),
        discharge=st.floats(min_value=0, max_value=10),
    )
    def test_soc_always_bounded_property(
        self,
        soc: float,
        charge: float,
        discharge: float,
    ) -> None:
        """Property: SoC should always remain within [0, max_capacity]."""
        # Create config inline to avoid fixture scope issues with hypothesis
        config = BatteryConfig(
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
        )
        try:
            result = update_soc(
                previous_soc_kwh=soc,
                pv_charged_kw=charge,
                grid_charged_kw=0.0,
                discharged_kw=discharge,
                config=config,
            )
            assert 0 <= result <= 100.0
        except SoCBoundsError:
            pass  # Expected for invalid charge/discharge amounts


# =============================================================================
# SINGLE TIMESTEP DISPATCH TESTS
# =============================================================================


class TestDispatchSingleTimestep:
    """Integration tests for dispatch_single_timestep function."""

    def test_basic_charging_scenario(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Sunny midday with no load should charge battery."""
        result = dispatch_single_timestep(
            solar_gen_kw=100.0,
            load_kw=0.0,
            previous_soc_kwh=0.0,
            hour=12,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert result.pv_charged_kw > 0
        assert result.soc_kwh > 0
        assert result.discharged_kw == 0

    def test_basic_discharging_scenario(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Evening with load and full battery should discharge."""
        result = dispatch_single_timestep(
            solar_gen_kw=0.0,
            load_kw=50.0,
            previous_soc_kwh=100.0,
            hour=18,
            config=default_battery_config,
            is_peak_period=True,
        )
        assert result.discharged_kw > 0
        assert result.soc_kwh < 100.0
        assert result.discharge_permitted

    def test_solar_meets_load_no_battery_action(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """If solar exactly meets load, battery should be passive."""
        result = dispatch_single_timestep(
            solar_gen_kw=50.0,
            load_kw=50.0,
            previous_soc_kwh=50.0,
            hour=20,  # Outside charging window
            config=default_battery_config,
            is_peak_period=False,
        )
        # No charging (outside window) and no discharge needed
        assert result.pv_charged_kw == 0
        assert result.discharged_kw == 0
        assert result.soc_kwh == 50.0

    def test_returns_battery_state_type(
        self, default_battery_config: BatteryConfig
    ) -> None:
        """Should return BatteryState namedtuple."""
        result = dispatch_single_timestep(
            solar_gen_kw=50.0,
            load_kw=50.0,
            previous_soc_kwh=50.0,
            hour=12,
            config=default_battery_config,
            is_peak_period=False,
        )
        assert isinstance(result, BatteryState)
        assert hasattr(result, "soc_kwh")
        assert hasattr(result, "pv_charged_kw")
        assert hasattr(result, "discharged_kw")
        assert hasattr(result, "discharge_permitted")

    def test_peak_shaving_mode(self, peak_shaving_config: BatteryConfig) -> None:
        """Peak shaving should discharge when load exceeds target."""
        result = dispatch_single_timestep(
            solar_gen_kw=0.0,
            load_kw=100.0,  # Above 80 kW target
            previous_soc_kwh=100.0,
            hour=14,
            config=peak_shaving_config,
            is_peak_period=False,
        )
        assert result.discharged_kw > 0
        assert result.discharge_permitted

    def test_energy_conservation(self, default_battery_config: BatteryConfig) -> None:
        """Energy should be conserved across timestep."""
        prev_soc = 50.0
        result = dispatch_single_timestep(
            solar_gen_kw=100.0,
            load_kw=30.0,
            previous_soc_kwh=prev_soc,
            hour=12,
            config=default_battery_config,
            is_peak_period=False,
        )

        # Calculate expected SoC change
        charged_kwh = result.pv_charged_kw * 1.0 * 0.95  # 1 hour, 95% eff
        discharged_kwh = result.discharged_kw * 1.0 / 0.95

        expected_soc = prev_soc + charged_kwh - discharged_kwh
        expected_soc = max(0, min(expected_soc, 100.0))

        assert result.soc_kwh == pytest.approx(expected_soc, abs=0.01)
