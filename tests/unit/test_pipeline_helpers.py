"""Unit tests for workbook-alignment helpers in pipeline.py."""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.pipeline import _build_dppa_net_generation, _normalize_hourly_price_columns_to_usd


def test_build_dppa_net_generation_includes_discharge() -> None:
    """DPPA net generation should follow the workbook's Calc!AB signal."""
    hourly = pd.DataFrame(
        {
            "solar_gen_kw": [10.0, 0.0],
            "pv_charged_kw": [3.0, 0.0],
            "discharged_kw": [2.0, 4.0],
        }
    )

    result = _build_dppa_net_generation(hourly)

    assert result.tolist() == pytest.approx([9.0, 4.0])


def test_normalize_hourly_price_columns_to_usd_converts_vnd_scale() -> None:
    """Workbook hourly prices in VND should be converted to USD/kWh."""
    hourly = pd.DataFrame(
        {
            "fmp_usd_per_kwh": [1300.0, 2600.0],
            "cfmp_usd_per_kwh": [1500.0, 2800.0],
        }
    )

    result = _normalize_hourly_price_columns_to_usd(hourly, exchange_rate_usd_vnd=26000.0)

    assert result["fmp_usd_per_kwh"].tolist() == pytest.approx([0.05, 0.1])
    assert result["cfmp_usd_per_kwh"].tolist() == pytest.approx(
        [1500.0 / 26000.0, 2800.0 / 26000.0]
    )


def test_normalize_hourly_price_columns_to_usd_leaves_usd_scale_unchanged() -> None:
    """Already-normalized hourly prices should not be divided again."""
    hourly = pd.DataFrame(
        {
            "fmp_usd_per_kwh": [0.05, 0.1],
            "cfmp_usd_per_kwh": [0.055, 0.11],
        }
    )

    result = _normalize_hourly_price_columns_to_usd(hourly, exchange_rate_usd_vnd=26000.0)

    assert result.equals(hourly)
