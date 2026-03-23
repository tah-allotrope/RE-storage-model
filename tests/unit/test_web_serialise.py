"""Unit tests for web function serialization helpers."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

FUNCTIONS_DIR = Path(__file__).resolve().parents[2] / "web" / "functions"
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.append(str(FUNCTIONS_DIR))

from utils.serialise import serialise_results  # noqa: E402


def test_serialise_results_sanitizes_nan_and_inf() -> None:
    input_results: dict[str, Any] = {
        "project_irr": math.nan,
        "equity_irr": math.inf,
        "npv_usd": 123.45,
        "_hourly_df": pd.DataFrame(
            {
                "datetime": ["2027-01-01T00:00:00", "2027-01-01T01:00:00"],
                "soc_kwh": [1.0, 2.0],
                "solar_gen_kw": [3.0, 4.0],
                "load_kw": [5.0, 6.0],
                "discharged_kw": [0.0, math.nan],
                "pv_charged_kw": [0.5, 0.25],
                "grid_load_after_re_kw": [4.5, 2.0],
            }
        ),
        "_lifetime_df": pd.DataFrame(
            {
                "year": [1, 2],
                "generation_mwh": [100.0, math.nan],
            }
        ),
        "_annual_df": pd.DataFrame(
            {
                "year": [1],
                "total_revenue_usd": [1000.0],
                "dscr": [math.nan],
                "free_cash_flow_to_equity_usd": [500.0],
            }
        ),
    }

    payload = serialise_results(input_results)

    assert payload["kpis"]["project_irr"] is None
    assert payload["kpis"]["equity_irr"] is None
    assert payload["kpis"]["npv_usd"] == 123.45
    assert payload["lifetime"][0]["year"] == 1
    assert payload["lifetime"][1]["generation_mwh"] is None
    assert payload["annual"][0]["dscr"] is None
    assert payload["cashflow"][0]["free_cash_flow_to_equity_usd"] == 500.0
    assert payload["dscr_series"][0]["year"] == 1
    assert payload["dispatch_sample"][1]["discharged_kw"] is None


def test_serialise_results_omits_private_non_dataframe_keys() -> None:
    input_results: dict[str, Any] = {
        "project_irr": 0.1,
        "_internal_note": "skip me",
    }

    payload = serialise_results(input_results)

    assert payload["kpis"] == {"project_irr": 0.1}
    assert payload["lifetime"] == []
    assert payload["annual"] == []
    assert payload["cashflow"] == []
    assert payload["dscr_series"] == []
    assert payload["dispatch_sample"] == []


def test_serialise_results_limits_dispatch_sample_to_first_week() -> None:
    input_results: dict[str, Any] = {
        "project_irr": 0.2,
        "_hourly_df": pd.DataFrame(
            {
                "datetime": pd.date_range("2027-01-01", periods=200, freq="h"),
                "soc_kwh": range(200),
                "solar_gen_kw": range(200),
                "load_kw": range(200),
                "discharged_kw": range(200),
                "pv_charged_kw": range(200),
                "grid_load_after_re_kw": range(200),
            }
        ),
    }

    payload = serialise_results(input_results)

    assert len(payload["dispatch_sample"]) == 168
    assert payload["dispatch_sample"][0]["datetime"] == "2027-01-01T00:00:00"
