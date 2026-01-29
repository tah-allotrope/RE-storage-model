"""
Unit tests for physics.solar module.

Tests cover:
1. Generation scaling
2. Direct PV consumption calculations
3. Surplus generation calculations
"""

import numpy as np
import pytest

from re_storage.physics.solar import (
    calculate_direct_pv_consumption,
    calculate_direct_pv_consumption_vectorized,
    calculate_surplus_generation,
    calculate_surplus_generation_vectorized,
    scale_generation,
)


class TestScaleGeneration:
    """Tests for scale_generation function."""

    def test_scale_factor_one_identity(self) -> None:
        """Scale factor of 1.0 should return identical values."""
        profile = [100.0, 200.0, 300.0]
        result = scale_generation(profile, scale_factor=1.0)
        np.testing.assert_array_almost_equal(result, profile)

    def test_scale_factor_doubles(self) -> None:
        """Scale factor of 2.0 should double all values."""
        profile = [100.0, 200.0, 300.0]
        result = scale_generation(profile, scale_factor=2.0)
        expected = [200.0, 400.0, 600.0]
        np.testing.assert_array_almost_equal(result, expected)

    def test_scale_factor_fractional(self) -> None:
        """Fractional scale factor should reduce values."""
        profile = [100.0, 200.0]
        result = scale_generation(profile, scale_factor=0.5)
        expected = [50.0, 100.0]
        np.testing.assert_array_almost_equal(result, expected)

    def test_accepts_numpy_array(self) -> None:
        """Should accept numpy arrays."""
        profile = np.array([100.0, 200.0])
        result = scale_generation(profile, scale_factor=1.5)
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, [150.0, 300.0])

    def test_zero_scale_factor_raises(self) -> None:
        """Zero scale factor should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            scale_generation([100.0], scale_factor=0.0)

    def test_negative_scale_factor_raises(self) -> None:
        """Negative scale factor should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            scale_generation([100.0], scale_factor=-1.0)


class TestCalculateDirectPvConsumption:
    """Tests for calculate_direct_pv_consumption function."""

    def test_solar_exceeds_load(self) -> None:
        """When solar > load, direct consumption = load."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=100.0,
            load_kw=50.0,
            pv_to_bess_kw=0.0,
        )
        assert result == 50.0

    def test_load_exceeds_solar(self) -> None:
        """When load > solar, direct consumption = solar."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=50.0,
            load_kw=100.0,
            pv_to_bess_kw=0.0,
        )
        assert result == 50.0

    def test_pv_to_bess_reduces_available(self) -> None:
        """PV to BESS should reduce available for load."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=100.0,
            load_kw=80.0,
            pv_to_bess_kw=30.0,
        )
        # Available = 100 - 30 = 70, load = 80, so direct = 70
        assert result == 70.0

    def test_pv_to_bess_exceeds_solar(self) -> None:
        """If PV to BESS > solar, direct consumption = 0."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=50.0,
            load_kw=100.0,
            pv_to_bess_kw=60.0,  # More than solar
        )
        assert result == 0.0

    def test_zero_solar(self) -> None:
        """Zero solar means zero direct consumption."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=0.0,
            load_kw=100.0,
            pv_to_bess_kw=0.0,
        )
        assert result == 0.0

    def test_zero_load(self) -> None:
        """Zero load means zero direct consumption."""
        result = calculate_direct_pv_consumption(
            solar_gen_kw=100.0,
            load_kw=0.0,
            pv_to_bess_kw=0.0,
        )
        assert result == 0.0

    def test_negative_solar_raises(self) -> None:
        """Negative solar should raise ValueError."""
        with pytest.raises(ValueError, match="solar_gen_kw cannot be negative"):
            calculate_direct_pv_consumption(
                solar_gen_kw=-10.0,
                load_kw=50.0,
                pv_to_bess_kw=0.0,
            )

    def test_negative_load_raises(self) -> None:
        """Negative load should raise ValueError."""
        with pytest.raises(ValueError, match="load_kw cannot be negative"):
            calculate_direct_pv_consumption(
                solar_gen_kw=100.0,
                load_kw=-50.0,
                pv_to_bess_kw=0.0,
            )


class TestCalculateDirectPvConsumptionVectorized:
    """Tests for vectorized direct PV consumption."""

    def test_matches_scalar_version(self) -> None:
        """Vectorized should match scalar for each element."""
        solar = np.array([100.0, 50.0, 200.0])
        load = np.array([80.0, 100.0, 150.0])
        pv2bess = np.array([20.0, 0.0, 100.0])

        result = calculate_direct_pv_consumption_vectorized(solar, load, pv2bess)

        # Check each element
        assert result[0] == 80.0  # min(80, max(100-20, 0)) = min(80, 80) = 80
        assert result[1] == 50.0  # min(100, max(50-0, 0)) = min(100, 50) = 50
        assert result[2] == 100.0  # min(150, max(200-100, 0)) = min(150, 100) = 100

    def test_negative_values_raise(self) -> None:
        """Negative values should raise ValueError."""
        with pytest.raises(ValueError, match="contains negative"):
            calculate_direct_pv_consumption_vectorized(
                solar_gen_kw=np.array([-10.0, 100.0]),
                load_kw=np.array([50.0, 50.0]),
                pv_to_bess_kw=np.array([0.0, 0.0]),
            )


class TestCalculateSurplusGeneration:
    """Tests for calculate_surplus_generation function."""

    def test_basic_surplus(self) -> None:
        """Basic surplus calculation."""
        result = calculate_surplus_generation(
            solar_gen_kw=100.0,
            direct_consumption_kw=60.0,
            pv_charged_kw=30.0,
        )
        assert result == 10.0

    def test_zero_surplus(self) -> None:
        """When all solar is used, surplus = 0."""
        result = calculate_surplus_generation(
            solar_gen_kw=100.0,
            direct_consumption_kw=60.0,
            pv_charged_kw=40.0,
        )
        assert result == 0.0

    def test_negative_surplus_raises(self) -> None:
        """Negative surplus indicates energy balance error."""
        with pytest.raises(ValueError, match="energy balance error"):
            calculate_surplus_generation(
                solar_gen_kw=100.0,
                direct_consumption_kw=60.0,
                pv_charged_kw=50.0,  # 60 + 50 = 110 > 100
            )

    def test_negative_inputs_raise(self) -> None:
        """Negative inputs should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_surplus_generation(
                solar_gen_kw=-100.0,
                direct_consumption_kw=60.0,
                pv_charged_kw=30.0,
            )


class TestCalculateSurplusGenerationVectorized:
    """Tests for vectorized surplus generation."""

    def test_matches_scalar_version(self) -> None:
        """Vectorized should match scalar results."""
        solar = np.array([100.0, 50.0, 200.0])
        direct = np.array([60.0, 30.0, 100.0])
        charged = np.array([30.0, 20.0, 50.0])

        result = calculate_surplus_generation_vectorized(solar, direct, charged)

        np.testing.assert_array_almost_equal(result, [10.0, 0.0, 50.0])

    def test_negative_surplus_raises(self) -> None:
        """Negative surplus at any timestep should raise."""
        solar = np.array([100.0, 50.0])
        direct = np.array([60.0, 30.0])
        charged = np.array([30.0, 30.0])  # Second: 50 - 30 - 30 = -10

        with pytest.raises(ValueError, match="Negative surplus"):
            calculate_surplus_generation_vectorized(solar, direct, charged)
