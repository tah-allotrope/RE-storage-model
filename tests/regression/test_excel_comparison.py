"""
Regression tests comparing Python outputs to Excel reference KPIs.

These tests are skipped unless both a model entrypoint and Excel fixture
are available in tests/data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from re_storage.pipeline import run_full_model
except ImportError:  # pragma: no cover - optional pipeline entrypoint
    run_full_model = None

REFERENCE_INPUT = Path(__file__).resolve().parents[1] / "data" / "excel_reference.xlsx"

EXPECTED_KPIS = {
    "project_irr": 0.0507,
    "equity_irr": 0.0464,
    "unlevered_irr": 0.0883,
    "npv_usd": -2_650_000.0,
}

TOLERANCES = {
    "irr": 0.0001,
    "npv_ratio": 0.0001,
}


def _get_metric(results: object, key: str) -> float:
    if isinstance(results, dict):
        if key not in results:
            raise AssertionError(f"Missing metric '{key}' in results dictionary.")
        return float(results[key])
    if hasattr(results, key):
        return float(getattr(results, key))
    if hasattr(results, "metrics") and isinstance(results.metrics, dict):
        if key not in results.metrics:
            raise AssertionError(f"Missing metric '{key}' in results.metrics dictionary.")
        return float(results.metrics[key])
    raise AssertionError(
        "Model results must expose metrics via dict, attributes, or .metrics dict."
    )


def test_regression_against_excel() -> None:
    if run_full_model is None:
        pytest.skip("Model pipeline entrypoint (run_full_model) is not available.")
    if not REFERENCE_INPUT.exists():
        pytest.skip("Excel reference fixture not found at tests/data/excel_reference.xlsx.")

    results = run_full_model(REFERENCE_INPUT)

    project_irr = _get_metric(results, "project_irr")
    equity_irr = _get_metric(results, "equity_irr")
    unlevered_irr = _get_metric(results, "unlevered_irr")
    npv_usd = _get_metric(results, "npv_usd")

    assert abs(project_irr - EXPECTED_KPIS["project_irr"]) <= TOLERANCES["irr"]
    assert abs(equity_irr - EXPECTED_KPIS["equity_irr"]) <= TOLERANCES["irr"]
    assert abs(unlevered_irr - EXPECTED_KPIS["unlevered_irr"]) <= TOLERANCES["irr"]

    expected_npv = EXPECTED_KPIS["npv_usd"]
    assert abs(npv_usd - expected_npv) / abs(expected_npv) <= TOLERANCES["npv_ratio"]
