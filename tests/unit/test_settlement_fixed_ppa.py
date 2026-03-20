"""
Unit tests for settlement.fixed_ppa module (Option 4 — Fixed EVN PPA).

Tests cover:
1. Basic revenue calculation against known values.
2. Curtailment reduces revenue proportionally.
3. Transmission loss reduces revenue proportionally.
4. Combined curtailment and tx loss.
5. Zero generation gives zero revenue.
6. Price unit conversion (USD/MWh → USD/kWh).
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.settlement.fixed_ppa import calculate_fixed_ppa_revenue


class TestCalculateFixedPpaRevenue:
    """Tests for calculate_fixed_ppa_revenue."""

    def test_basic_calculation(self) -> None:
        # 1 MWh (1000 kW for 1 h) at $70/MWh = $70
        solar_gen = pd.Series([1000.0])
        revenue = calculate_fixed_ppa_revenue(solar_gen, fixed_price_usd_per_mwh=70.0)
        assert revenue.iloc[0] == pytest.approx(70.0)

    def test_price_conversion_mwh_to_kwh(self) -> None:
        # $70/MWh = $0.07/kWh; 100 kWh × $0.07 = $7
        solar_gen = pd.Series([100.0])
        revenue = calculate_fixed_ppa_revenue(solar_gen, fixed_price_usd_per_mwh=70.0)
        assert revenue.iloc[0] == pytest.approx(7.0)

    def test_curtailment_reduces_revenue(self) -> None:
        solar_gen = pd.Series([1000.0])
        rev_no_curt = calculate_fixed_ppa_revenue(solar_gen, curtailment_pct=0.0)
        rev_with_curt = calculate_fixed_ppa_revenue(solar_gen, curtailment_pct=0.10)
        assert rev_with_curt.iloc[0] == pytest.approx(rev_no_curt.iloc[0] * 0.90)

    def test_tx_loss_reduces_revenue(self) -> None:
        solar_gen = pd.Series([1000.0])
        rev_no_loss = calculate_fixed_ppa_revenue(solar_gen, tx_loss_pct=0.0)
        rev_with_loss = calculate_fixed_ppa_revenue(solar_gen, tx_loss_pct=0.05)
        assert rev_with_loss.iloc[0] == pytest.approx(rev_no_loss.iloc[0] * 0.95)

    def test_combined_curtailment_and_tx_loss(self) -> None:
        solar_gen = pd.Series([1000.0])
        revenue = calculate_fixed_ppa_revenue(
            solar_gen,
            fixed_price_usd_per_mwh=70.0,
            curtailment_pct=0.10,
            tx_loss_pct=0.05,
        )
        # 1000 × (70/1000) × (1-0.1) × (1-0.05) = 70 × 0.9 × 0.95 = 59.85
        assert revenue.iloc[0] == pytest.approx(59.85)

    def test_zero_generation_gives_zero(self) -> None:
        solar_gen = pd.Series([0.0] * 5)
        revenue = calculate_fixed_ppa_revenue(solar_gen)
        assert (revenue == 0.0).all()

    def test_vectorised_over_8760_hours(self) -> None:
        import numpy as np
        solar_gen = pd.Series(np.full(8760, 100.0))
        revenue = calculate_fixed_ppa_revenue(solar_gen, fixed_price_usd_per_mwh=70.0)
        assert len(revenue) == 8760
        assert revenue.sum() == pytest.approx(8760 * 100.0 * 0.07, rel=1e-9)
