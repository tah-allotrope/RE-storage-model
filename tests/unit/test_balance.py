"""
Unit tests for physics.balance module.

Tests cover:
1. Energy balance validation
2. SoC bounds validation
3. Power rating validation

These tests enforce the "Physics First" principle.
"""

import numpy as np
import pytest

from re_storage.core.exceptions import (
    EnergyBalanceError,
    InsufficientCapacityError,
    SoCBoundsError,
)
from re_storage.physics.balance import (
    validate_energy_balance,
    validate_energy_balance_vectorized,
    validate_power_rating,
    validate_soc_bounds,
    validate_soc_bounds_vectorized,
)


class TestValidateEnergyBalance:
    """Tests for validate_energy_balance function."""

    def test_balanced_passes(self) -> None:
        """Balanced energy should not raise."""
        validate_energy_balance(
            solar_gen_kwh=100.0,
            direct_consumption_kwh=60.0,
            charged_kwh=30.0,
            surplus_kwh=10.0,
        )
        # No exception means pass

    def test_imbalance_raises(self) -> None:
        """Imbalanced energy should raise EnergyBalanceError."""
        with pytest.raises(EnergyBalanceError, match="Energy balance failed"):
            validate_energy_balance(
                solar_gen_kwh=100.0,
                direct_consumption_kwh=60.0,
                charged_kwh=30.0,
                surplus_kwh=20.0,  # 60 + 30 + 20 = 110 != 100
            )

    def test_small_imbalance_within_tolerance(self) -> None:
        """Small imbalance within tolerance should pass."""
        validate_energy_balance(
            solar_gen_kwh=100.0,
            direct_consumption_kwh=60.0,
            charged_kwh=30.0,
            surplus_kwh=10.0005,  # 0.0005 kWh difference
            tolerance=0.001,
        )

    def test_imbalance_exceeds_tolerance(self) -> None:
        """Imbalance exceeding tolerance should raise."""
        with pytest.raises(EnergyBalanceError):
            validate_energy_balance(
                solar_gen_kwh=100.0,
                direct_consumption_kwh=60.0,
                charged_kwh=30.0,
                surplus_kwh=10.01,  # 0.01 kWh difference
                tolerance=0.001,
            )

    def test_error_includes_timestep(self) -> None:
        """Error should include timestep when provided."""
        with pytest.raises(EnergyBalanceError, match="timestep 42"):
            validate_energy_balance(
                solar_gen_kwh=100.0,
                direct_consumption_kwh=60.0,
                charged_kwh=30.0,
                surplus_kwh=20.0,
                timestep=42,
            )

    def test_error_attributes(self) -> None:
        """Error should have imbalance and timestep attributes."""
        try:
            validate_energy_balance(
                solar_gen_kwh=100.0,
                direct_consumption_kwh=60.0,
                charged_kwh=30.0,
                surplus_kwh=20.0,
                timestep=42,
            )
        except EnergyBalanceError as e:
            assert e.imbalance_kwh is not None
            assert abs(e.imbalance_kwh - (-10.0)) < 0.001  # 100 - 110 = -10
            assert e.timestep == 42


class TestValidateEnergyBalanceVectorized:
    """Tests for vectorized energy balance validation."""

    def test_all_balanced_passes(self) -> None:
        """All balanced timesteps should pass."""
        validate_energy_balance_vectorized(
            solar_gen_kwh=np.array([100.0, 200.0, 150.0]),
            direct_consumption_kwh=np.array([60.0, 100.0, 80.0]),
            charged_kwh=np.array([30.0, 80.0, 50.0]),
            surplus_kwh=np.array([10.0, 20.0, 20.0]),
        )

    def test_one_imbalanced_raises(self) -> None:
        """Single imbalanced timestep should raise."""
        with pytest.raises(EnergyBalanceError, match="1 timesteps"):
            validate_energy_balance_vectorized(
                solar_gen_kwh=np.array([100.0, 200.0]),
                direct_consumption_kwh=np.array([60.0, 100.0]),
                charged_kwh=np.array([30.0, 80.0]),
                surplus_kwh=np.array([10.0, 30.0]),  # Second: 200 != 210
            )

    def test_multiple_imbalanced_reports_count(self) -> None:
        """Multiple imbalanced timesteps should report count."""
        with pytest.raises(EnergyBalanceError, match="2 timesteps"):
            validate_energy_balance_vectorized(
                solar_gen_kwh=np.array([100.0, 200.0]),
                direct_consumption_kwh=np.array([60.0, 100.0]),
                charged_kwh=np.array([50.0, 80.0]),  # Both wrong
                surplus_kwh=np.array([10.0, 30.0]),
            )


class TestValidateSocBounds:
    """Tests for validate_soc_bounds function."""

    def test_valid_soc_passes(self) -> None:
        """Valid SoC within bounds should not raise."""
        validate_soc_bounds(soc_kwh=50.0, max_capacity_kwh=100.0)
        validate_soc_bounds(soc_kwh=0.0, max_capacity_kwh=100.0)
        validate_soc_bounds(soc_kwh=100.0, max_capacity_kwh=100.0)

    def test_negative_soc_raises(self) -> None:
        """Negative SoC should raise SoCBoundsError."""
        with pytest.raises(SoCBoundsError, match="Negative SoC"):
            validate_soc_bounds(soc_kwh=-5.0, max_capacity_kwh=100.0)

    def test_exceeds_capacity_raises(self) -> None:
        """SoC exceeding capacity should raise SoCBoundsError."""
        with pytest.raises(SoCBoundsError, match="exceeds capacity"):
            validate_soc_bounds(soc_kwh=110.0, max_capacity_kwh=100.0)

    def test_tolerance_for_floating_point(self) -> None:
        """Small violations within tolerance should pass."""
        validate_soc_bounds(
            soc_kwh=-0.0005,  # Slightly negative
            max_capacity_kwh=100.0,
            tolerance=0.001,
        )
        validate_soc_bounds(
            soc_kwh=100.0005,  # Slightly over
            max_capacity_kwh=100.0,
            tolerance=0.001,
        )

    def test_error_includes_timestep(self) -> None:
        """Error should include timestep when provided."""
        with pytest.raises(SoCBoundsError, match="timestep 99"):
            validate_soc_bounds(
                soc_kwh=-10.0,
                max_capacity_kwh=100.0,
                timestep=99,
            )

    def test_error_attributes(self) -> None:
        """Error should have soc, capacity, and timestep attributes."""
        try:
            validate_soc_bounds(
                soc_kwh=-10.0,
                max_capacity_kwh=100.0,
                timestep=99,
            )
        except SoCBoundsError as e:
            assert e.soc_kwh == -10.0
            assert e.max_capacity_kwh == 100.0
            assert e.timestep == 99


class TestValidateSocBoundsVectorized:
    """Tests for vectorized SoC bounds validation."""

    def test_all_valid_passes(self) -> None:
        """All valid SoC values should pass."""
        validate_soc_bounds_vectorized(
            soc_kwh=np.array([0.0, 50.0, 100.0]),
            max_capacity_kwh=100.0,
        )

    def test_negative_raises(self) -> None:
        """Negative SoC should raise."""
        with pytest.raises(SoCBoundsError, match="Negative SoC"):
            validate_soc_bounds_vectorized(
                soc_kwh=np.array([50.0, -5.0, 30.0]),
                max_capacity_kwh=100.0,
            )

    def test_exceeds_capacity_raises(self) -> None:
        """SoC exceeding capacity should raise."""
        with pytest.raises(SoCBoundsError, match="exceeds capacity"):
            validate_soc_bounds_vectorized(
                soc_kwh=np.array([50.0, 110.0, 30.0]),
                max_capacity_kwh=100.0,
            )

    def test_reports_violation_count(self) -> None:
        """Should report number of violations."""
        with pytest.raises(SoCBoundsError, match="2 timesteps"):
            validate_soc_bounds_vectorized(
                soc_kwh=np.array([-5.0, 50.0, -10.0]),
                max_capacity_kwh=100.0,
            )


class TestValidatePowerRating:
    """Tests for validate_power_rating function."""

    def test_within_rating_passes(self) -> None:
        """Power within rating should not raise."""
        validate_power_rating(
            power_kw=80.0,
            max_rating_kw=100.0,
            equipment_name="inverter",
        )

    def test_at_rating_passes(self) -> None:
        """Power exactly at rating should pass."""
        validate_power_rating(
            power_kw=100.0,
            max_rating_kw=100.0,
            equipment_name="inverter",
        )

    def test_exceeds_rating_raises(self) -> None:
        """Power exceeding rating should raise."""
        with pytest.raises(InsufficientCapacityError, match="inverter.*exceeded"):
            validate_power_rating(
                power_kw=120.0,
                max_rating_kw=100.0,
                equipment_name="inverter",
            )

    def test_tolerance_allows_small_overshoot(self) -> None:
        """Small overshoot within tolerance should pass."""
        validate_power_rating(
            power_kw=105.0,
            max_rating_kw=100.0,
            equipment_name="inverter",
            tolerance=0.1,  # 10% tolerance
        )

    def test_tolerance_exceeded_raises(self) -> None:
        """Overshoot exceeding tolerance should raise."""
        with pytest.raises(InsufficientCapacityError):
            validate_power_rating(
                power_kw=115.0,
                max_rating_kw=100.0,
                equipment_name="inverter",
                tolerance=0.1,  # 10% tolerance, but 15% over
            )

    def test_error_includes_timestep(self) -> None:
        """Error should include timestep when provided."""
        with pytest.raises(InsufficientCapacityError, match="timestep 500"):
            validate_power_rating(
                power_kw=150.0,
                max_rating_kw=100.0,
                equipment_name="grid_connection",
                timestep=500,
            )

    def test_error_attributes(self) -> None:
        """Error should have requested and available power attributes."""
        try:
            validate_power_rating(
                power_kw=150.0,
                max_rating_kw=100.0,
                equipment_name="inverter",
            )
        except InsufficientCapacityError as e:
            assert e.requested_kw == 150.0
            assert e.available_kw == 100.0

    def test_zero_rating_raises(self) -> None:
        """Zero max rating should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_power_rating(
                power_kw=50.0,
                max_rating_kw=0.0,
                equipment_name="inverter",
            )
