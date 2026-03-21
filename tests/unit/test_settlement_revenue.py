"""
Unit tests for settlement.revenue — PpaMode enum and calculate_revenue dispatcher.

Tests cover:
1. PpaMode enum values match Excel option integers (1-4).
2. PpaMode.from_excel_option() round-trips for all valid values.
3. PpaMode.from_excel_option() raises ValueError for invalid inputs.
4. calculate_revenue dispatches to bundled (Option 1) and produces expected column.
5. calculate_revenue dispatches to separate (Option 2) and produces expected column.
6. calculate_revenue dispatches to DPPA CfD (Option 3, default) and produces columns.
7. calculate_revenue dispatches to fixed PPA (Option 4) and produces expected column.
8. Integer mode argument is accepted alongside PpaMode members.
9. calculate_revenue does not mutate the input DataFrame.
10. Invalid integer mode raises ValueError.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.types import TimePeriod
from re_storage.inputs.schemas import SystemAssumptions
from re_storage.settlement.revenue import PpaMode, calculate_revenue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TARIFF_RATES: dict[TimePeriod, float] = {
    TimePeriod.OFF_PEAK: 0.05,
    TimePeriod.STANDARD: 0.10,
    TimePeriod.PEAK: 0.20,
}


def _make_assumptions(**overrides) -> SystemAssumptions:
    """Build a minimal SystemAssumptions for testing."""
    defaults = {
        "simulation_capacity_kwp": 100.0,
        "actual_capacity_kwp": 100.0,
        "usable_bess_capacity_kwh": 200.0,
        "bess_power_rating_kw": 100.0,
        "charge_efficiency": 0.95,
        "discharge_efficiency": 0.95,
        "strategy_mode": 1,
        "charging_mode": 1,
        "charge_start_hour": 9,
        "charge_end_hour": 15,
        "precharge_target_hour": 17,
        "precharge_target_soc_kwh": 150.0,
        "min_direct_pv_share": 0.1,
        "active_pv2bess_share": 0.8,
        "demand_reduction_target": 0.2,
        "strike_price_usd_per_kwh": 0.08,
        "k_factor": 0.98,
        "kpp": 1.05,
        "bess_enabled": True,
        "dppa_enabled": True,
        # PPA option params
        "ppa_option": 3,
        "bundled_discount_pct": 0.15,
        "pv_discount_pct": 0.05,
        "bess_discount_pct": 0.10,
        "fixed_ppa_price_usd_per_mwh": 70.0,
    }
    defaults.update(overrides)
    return SystemAssumptions(**defaults)


def _make_hourly_data(n: int = 2) -> pd.DataFrame:
    """Build a minimal hourly DataFrame with all columns that may be needed."""
    return pd.DataFrame(
        {
            "direct_pv_consumption_kw": [100.0] * n,
            "discharged_kw": [50.0] * n,
            "solar_gen_kw": [150.0] * n,
            "time_period": [TimePeriod.STANDARD] * n,
            # DPPA columns (Option 3 only)
            "net_gen_for_dppa_kwh": [100.0] * n,
            "load_kwh": [200.0] * n,
            "fmp_usd_per_kwh": [0.03] * n,
        }
    )


# ---------------------------------------------------------------------------
# PpaMode enum
# ---------------------------------------------------------------------------


class TestPpaMode:
    """Tests for PpaMode enum definition and helpers."""

    def test_option_values_match_excel_integers(self) -> None:
        """Enum integer values must match Assumption!Q20 option numbers."""
        assert PpaMode.BUNDLED_DISCOUNT.value == 1
        assert PpaMode.SEPARATE_PV_BESS.value == 2
        assert PpaMode.DPPA_CFD.value == 3
        assert PpaMode.FIXED_PPA.value == 4

    def test_from_excel_option_round_trips(self) -> None:
        """from_excel_option should return the correct member for 1-4."""
        for expected in PpaMode:
            result = PpaMode.from_excel_option(expected.value)
            assert result is expected

    def test_from_excel_option_invalid_raises(self) -> None:
        """out-of-range option numbers must raise ValueError."""
        with pytest.raises(ValueError, match="must be one of"):
            PpaMode.from_excel_option(0)
        with pytest.raises(ValueError, match="must be one of"):
            PpaMode.from_excel_option(5)

    def test_int_enum_comparison(self) -> None:
        """PpaMode members compare equal to their integer values (IntEnum)."""
        assert PpaMode.DPPA_CFD == 3
        assert PpaMode.BUNDLED_DISCOUNT < PpaMode.FIXED_PPA


# ---------------------------------------------------------------------------
# calculate_revenue dispatcher
# ---------------------------------------------------------------------------


class TestCalculateRevenue:
    """Tests for calculate_revenue dispatcher."""

    # -- Option 1: Bundled Discount --

    def test_option1_bundled_produces_dppa_revenue_column(self) -> None:
        """Option 1 must produce a 'dppa_revenue_usd' column."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions(bundled_discount_pct=0.15)
        result = calculate_revenue(
            PpaMode.BUNDLED_DISCOUNT, hourly, assumptions, _TARIFF_RATES
        )
        assert "dppa_revenue_usd" in result.columns

    def test_option1_bundled_revenue_value(self) -> None:
        """Option 1: (100 + 50) kW × $0.10/kWh × (1 - 0.15) = $12.75."""
        hourly = _make_hourly_data(1)
        assumptions = _make_assumptions(bundled_discount_pct=0.15)
        result = calculate_revenue(
            PpaMode.BUNDLED_DISCOUNT, hourly, assumptions, _TARIFF_RATES
        )
        expected = 150.0 * 0.10 * (1.0 - 0.15)  # 12.75
        assert result["dppa_revenue_usd"].iloc[0] == pytest.approx(expected)

    # -- Option 2: Separate PV + BESS --

    def test_option2_separate_produces_dppa_revenue_column(self) -> None:
        """Option 2 must produce a 'dppa_revenue_usd' column."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions(pv_discount_pct=0.05, bess_discount_pct=0.10)
        result = calculate_revenue(
            PpaMode.SEPARATE_PV_BESS, hourly, assumptions, _TARIFF_RATES
        )
        assert "dppa_revenue_usd" in result.columns

    def test_option2_separate_pv_bess_revenue_value(self) -> None:
        """Option 2: PV: 100 × 0.10 × 0.95 = 9.5; BESS: 50 × 0.10 × 0.90 = 4.5; total = 14."""
        hourly = _make_hourly_data(1)
        assumptions = _make_assumptions(pv_discount_pct=0.05, bess_discount_pct=0.10)
        result = calculate_revenue(
            PpaMode.SEPARATE_PV_BESS, hourly, assumptions, _TARIFF_RATES
        )
        expected = (100.0 * 0.10 * 0.95) + (50.0 * 0.10 * 0.90)  # 9.5 + 4.5 = 14.0
        assert result["dppa_revenue_usd"].iloc[0] == pytest.approx(expected)

    def test_option2_different_discounts_give_different_result_to_option1(self) -> None:
        """Option 2 with split discounts should differ from Option 1 bundled."""
        hourly = _make_hourly_data(2)
        # Use large PV discount (30%) and small BESS discount (5%) so the
        # separate-pricing total is clearly less than a flat bundled-10% rate.
        # Bundled 10%: 150 × 0.10 × 0.90 = 13.5 per row → total = 27.0
        # Separate: PV 100 × 0.10 × 0.70 + BESS 50 × 0.10 × 0.95 = 7.0 + 4.75 = 11.75 → total = 23.5
        assumptions = _make_assumptions(
            bundled_discount_pct=0.10,
            pv_discount_pct=0.30,
            bess_discount_pct=0.05,
        )
        rev1 = calculate_revenue(
            PpaMode.BUNDLED_DISCOUNT, hourly, assumptions, _TARIFF_RATES
        )["dppa_revenue_usd"].sum()
        rev2 = calculate_revenue(
            PpaMode.SEPARATE_PV_BESS, hourly, assumptions, _TARIFF_RATES
        )["dppa_revenue_usd"].sum()
        assert rev1 != pytest.approx(rev2, rel=1e-3)
        # Bundled 10% vs high-PV-discount separate: bundled should be higher
        assert rev1 > rev2

    # -- Option 3: DPPA CfD (default) --

    def test_option3_dppa_produces_dppa_revenue_column(self) -> None:
        """Option 3 must produce 'dppa_revenue_usd' and intermediate DPPA columns."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions()
        result = calculate_revenue(
            PpaMode.DPPA_CFD, hourly, assumptions, _TARIFF_RATES
        )
        assert "dppa_revenue_usd" in result.columns
        # DPPA-specific intermediate columns should also be present
        assert "market_revenue_usd" in result.columns
        assert "cfd_settlement_usd" in result.columns

    def test_option3_revenue_matches_total_dppa_revenue(self) -> None:
        """dppa_revenue_usd must equal total_dppa_revenue_usd from the DPPA module."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions()
        result = calculate_revenue(
            PpaMode.DPPA_CFD, hourly, assumptions, _TARIFF_RATES
        )
        pd.testing.assert_series_equal(
            result["dppa_revenue_usd"].reset_index(drop=True),
            result["total_dppa_revenue_usd"].reset_index(drop=True),
            check_names=False,
        )

    # -- Option 4: Fixed PPA --

    def test_option4_fixed_ppa_produces_dppa_revenue_column(self) -> None:
        """Option 4 must produce a 'dppa_revenue_usd' column."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions(fixed_ppa_price_usd_per_mwh=70.0)
        result = calculate_revenue(
            PpaMode.FIXED_PPA, hourly, assumptions, _TARIFF_RATES
        )
        assert "dppa_revenue_usd" in result.columns

    def test_option4_fixed_ppa_revenue_value(self) -> None:
        """Option 4: 150 kW × ($70/1000) = $10.50."""
        hourly = _make_hourly_data(1)
        assumptions = _make_assumptions(fixed_ppa_price_usd_per_mwh=70.0)
        result = calculate_revenue(
            PpaMode.FIXED_PPA, hourly, assumptions, _TARIFF_RATES
        )
        # solar_gen_kw = 150, fixed price = $0.07/kWh → 150 × 0.07 = $10.50
        assert result["dppa_revenue_usd"].iloc[0] == pytest.approx(10.50)

    # -- Integer mode argument --

    def test_integer_mode_accepted(self) -> None:
        """Raw int (1-4) should be accepted and dispatch identically to PpaMode member."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions(bundled_discount_pct=0.15)
        result_enum = calculate_revenue(
            PpaMode.BUNDLED_DISCOUNT, hourly, assumptions, _TARIFF_RATES
        )
        result_int = calculate_revenue(1, hourly, assumptions, _TARIFF_RATES)
        pd.testing.assert_series_equal(
            result_enum["dppa_revenue_usd"].reset_index(drop=True),
            result_int["dppa_revenue_usd"].reset_index(drop=True),
        )

    def test_invalid_integer_mode_raises(self) -> None:
        """Unsupported integer mode must raise ValueError."""
        hourly = _make_hourly_data()
        assumptions = _make_assumptions()
        with pytest.raises(ValueError):
            calculate_revenue(99, hourly, assumptions, _TARIFF_RATES)

    # -- Immutability --

    def test_does_not_mutate_input(self) -> None:
        """Input DataFrame must not be mutated by any dispatch branch."""
        for mode in PpaMode:
            hourly = _make_hourly_data()
            original_cols = hourly.columns.tolist()
            calculate_revenue(mode, hourly, _make_assumptions(), _TARIFF_RATES)
            assert hourly.columns.tolist() == original_cols, (
                f"Input was mutated for mode {mode}"
            )

    # -- Default mode is DPPA --

    def test_mode_3_is_dppa_cfd(self) -> None:
        """PpaMode(3) must be DPPA_CFD (preserves existing default behaviour)."""
        assert PpaMode(3) is PpaMode.DPPA_CFD
