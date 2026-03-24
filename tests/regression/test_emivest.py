"""Regression tests for Emivest JSON+CSV project input."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from re_storage.pipeline import run_model_from_json

PROJECT_DIR = Path(__file__).resolve().parents[1] / "data" / "projects" / "emivest"
REFERENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "references" / "emivest.json"

TOLERANCE_ABSOLUTE_IRR = 0.0001
TOLERANCE_RELATIVE_ENERGY = 0.0001
TOLERANCE_RELATIVE_REVENUE = 0.0001
TOLERANCE_ABSOLUTE_DSCR = 0.001
TOLERANCE_RELATIVE_NPV = 0.0001

KPI_TOLERANCES: dict[str, tuple[str, float]] = {
    "project_irr": ("abs", TOLERANCE_ABSOLUTE_IRR),
    "equity_irr": ("abs", TOLERANCE_ABSOLUTE_IRR),
    "unlevered_irr": ("abs", TOLERANCE_ABSOLUTE_IRR),
    "npv_usd": ("rel", TOLERANCE_RELATIVE_NPV),
    "dscr_min": ("abs", TOLERANCE_ABSOLUTE_DSCR),
    "calc_solar_gen_sum_kwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "calc_soc_min_kwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "calc_soc_max_kwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "year1_solar_generation_mwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "year1_dppa_revenue_usd": ("rel", TOLERANCE_RELATIVE_REVENUE),
    "year1_grid_savings_usd": ("rel", TOLERANCE_RELATIVE_REVENUE),
    "year1_opex_usd": ("rel", TOLERANCE_RELATIVE_REVENUE),
    "year1_ebitda_usd": ("rel", TOLERANCE_RELATIVE_REVENUE),
}


def _compare_kpi(
    kpi_key: str,
    actual: float,
    expected: float,
    mode: str,
    tolerance: float,
) -> tuple[bool, str]:
    if expected is None or actual is None:
        return True, f"{kpi_key}: skipped (None reference)"

    if math.isnan(actual):
        return False, f"{kpi_key}: actual=nan, expected={expected}"

    if math.isnan(expected):
        return True, f"{kpi_key}: skipped (NaN reference)"

    if mode == "abs":
        diff = abs(actual - expected)
        return diff <= tolerance, (
            f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
            f"abs_diff={diff:.6f}, tolerance={tolerance:.6f}"
        )

    if abs(expected) < 1e-12:
        diff = abs(actual - expected)
        return diff <= tolerance, (
            f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
            f"abs_diff={diff:.6f} (expected≈0, tolerance={tolerance:.6f})"
        )

    diff = abs(actual - expected) / abs(expected)
    return diff <= tolerance, (
        f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
        f"rel_diff={diff:.6%}, tolerance={tolerance:.4%}"
    )


class TestEmivestRegression:
    def test_compare_kpi_fails_on_nan_actual(self) -> None:
        passed, detail = _compare_kpi("equity_irr", float("nan"), 0.12, "abs", 0.0001)

        assert passed is False
        assert "actual=nan" in detail

    def test_model_runs_without_error(self) -> None:
        results = run_model_from_json(PROJECT_DIR)
        assert isinstance(results, dict)

    def test_kpi_dict_has_expected_keys(self) -> None:
        results = run_model_from_json(PROJECT_DIR)
        expected_keys = {
            "project_irr",
            "equity_irr",
            "unlevered_irr",
            "npv_usd",
            "dscr_min",
            "calc_solar_gen_sum_kwh",
            "calc_soc_min_kwh",
            "calc_soc_max_kwh",
            "year1_solar_generation_mwh",
            "year1_dppa_revenue_usd",
            "year1_grid_savings_usd",
            "year1_opex_usd",
            "year1_ebitda_usd",
        }
        assert expected_keys.issubset(set(results.keys()))

    def test_solar_generation_reasonable(self) -> None:
        results = run_model_from_json(PROJECT_DIR)
        value = float(results["year1_solar_generation_mwh"])
        assert 3000.0 <= value <= 6000.0

    def test_soc_bounds(self) -> None:
        results = run_model_from_json(PROJECT_DIR)
        assert float(results["calc_soc_min_kwh"]) >= 0.0
        assert float(results["calc_soc_max_kwh"]) <= 1827.5

    def test_irr_values_reasonable(self) -> None:
        results = run_model_from_json(PROJECT_DIR)
        assert -0.5 <= float(results["project_irr"]) <= 1.0
        assert -0.5 <= float(results["equity_irr"]) <= 1.0

    def test_all_kpis_against_reference(self) -> None:
        reference: dict[str, Any] = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        results = run_model_from_json(PROJECT_DIR)

        failures: list[str] = []
        for kpi_key, (mode, tolerance) in KPI_TOLERANCES.items():
            expected = reference.get(kpi_key)
            actual = results.get(kpi_key)
            if expected is None or actual is None:
                continue

            passed, detail = _compare_kpi(kpi_key, float(actual), float(expected), mode, tolerance)
            if not passed:
                failures.append(detail)

        if failures:
            pytest.fail("Emivest KPI mismatches:\n" + "\n".join(f"  FAIL: {f}" for f in failures))
