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
        "_hourly_df": pd.DataFrame({"x": [1.0, 2.0]}),
        "_lifetime_df": pd.DataFrame(
            {
                "year": [1, 2],
                "generation_mwh": [100.0, math.nan],
            }
        ),
    }

    payload = serialise_results(input_results)

    assert payload["kpis"]["project_irr"] is None
    assert payload["kpis"]["equity_irr"] is None
    assert payload["kpis"]["npv_usd"] == 123.45
    assert payload["lifetime"][0]["year"] == 1
    assert payload["lifetime"][1]["generation_mwh"] is None


def test_serialise_results_omits_private_non_dataframe_keys() -> None:
    input_results: dict[str, Any] = {
        "project_irr": 0.1,
        "_internal_note": "skip me",
    }

    payload = serialise_results(input_results)

    assert payload["kpis"] == {"project_irr": 0.1}
    assert payload["lifetime"] == []
