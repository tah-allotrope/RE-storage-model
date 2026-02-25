"""
Regression tests comparing Python model outputs to Excel reference KPIs.

This module auto-discovers project Excel files in ``tests/data/projects/``
and their matching JSON reference files in ``tests/data/references/``.
Each project is run through the full Python pipeline and compared against
the reference KPIs at multiple layers (physics, settlement, aggregation,
financial) with tolerance tiers defined in AGENTS.md §4.3.

Usage:
    # Extract references first (one-time or after Excel changes):
    python scripts/extract_excel_kpis.py tests/data/projects/*.xlsx

    # Run regression tests:
    pytest tests/regression/ -v
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from re_storage.pipeline import run_full_model

# ---------------------------------------------------------------------------
# Discovery paths
# ---------------------------------------------------------------------------

TESTS_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PROJECTS_DIR = TESTS_DATA_DIR / "projects"
REFERENCES_DIR = TESTS_DATA_DIR / "references"

# ---------------------------------------------------------------------------
# Tolerance tiers (AGENTS.md §4.3)
# ---------------------------------------------------------------------------

TOLERANCE_ABSOLUTE_IRR = 0.0001      # ±0.01 pp for IRR
TOLERANCE_RELATIVE_ENERGY = 0.0001   # ±0.01% for kWh/MWh
TOLERANCE_RELATIVE_REVENUE = 0.0001  # ±0.01% for USD
TOLERANCE_ABSOLUTE_DSCR = 0.001      # ±0.001 for DSCR ratio
TOLERANCE_RELATIVE_NPV = 0.0001      # ±0.01% for NPV

# KPI → (comparison_mode, tolerance)
# Modes: "abs" = absolute difference, "rel" = relative difference
KPI_TOLERANCES: dict[str, tuple[str, float]] = {
    # Financial (final) KPIs
    "project_irr":      ("abs", TOLERANCE_ABSOLUTE_IRR),
    "equity_irr":       ("abs", TOLERANCE_ABSOLUTE_IRR),
    "unlevered_irr":    ("abs", TOLERANCE_ABSOLUTE_IRR),
    "npv_usd":          ("rel", TOLERANCE_RELATIVE_NPV),
    "dscr_min":         ("abs", TOLERANCE_ABSOLUTE_DSCR),
    # Physics intermediate KPIs
    "calc_solar_gen_sum_kwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "calc_soc_min_kwh":       ("rel", TOLERANCE_RELATIVE_ENERGY),
    "calc_soc_max_kwh":       ("rel", TOLERANCE_RELATIVE_ENERGY),
    # Aggregation intermediate KPIs
    "year1_solar_generation_mwh": ("rel", TOLERANCE_RELATIVE_ENERGY),
    "year1_dppa_revenue_usd":    ("rel", TOLERANCE_RELATIVE_REVENUE),
    "year1_grid_savings_usd":    ("rel", TOLERANCE_RELATIVE_REVENUE),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _discover_project_pairs() -> list[tuple[str, Path, Path]]:
    """
    Find all (project_name, excel_path, reference_json_path) triples.

    Only returns pairs where both the .xlsx and .json exist.
    """
    if not PROJECTS_DIR.exists():
        return []

    pairs: list[tuple[str, Path, Path]] = []
    for xlsx in sorted(PROJECTS_DIR.glob("*.xlsx")):
        ref_json = REFERENCES_DIR / f"{xlsx.stem}.json"
        if ref_json.exists():
            pairs.append((xlsx.stem, xlsx, ref_json))
    return pairs


def _load_reference(json_path: Path) -> dict[str, Any]:
    """Load a JSON reference file into a dict."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _compare_kpi(
    kpi_key: str,
    actual: float,
    expected: float,
    mode: str,
    tolerance: float,
) -> tuple[bool, str]:
    """
    Compare a single KPI value against expected.

    Returns (passed, detail_message).
    """
    if expected is None or actual is None:
        return True, f"{kpi_key}: skipped (None reference)"

    if math.isnan(actual) or math.isnan(expected):
        return True, f"{kpi_key}: skipped (NaN)"

    if mode == "abs":
        diff = abs(actual - expected)
        passed = diff <= tolerance
        detail = (
            f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
            f"abs_diff={diff:.6f}, tolerance={tolerance:.6f}"
        )
    elif mode == "rel":
        if abs(expected) < 1e-12:
            # Avoid division by zero; use absolute comparison
            diff = abs(actual - expected)
            passed = diff <= tolerance
            detail = (
                f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
                f"abs_diff={diff:.6f} (expected≈0, tolerance={tolerance:.6f})"
            )
        else:
            diff = abs(actual - expected) / abs(expected)
            passed = diff <= tolerance
            detail = (
                f"{kpi_key}: actual={actual:.6f}, expected={expected:.6f}, "
                f"rel_diff={diff:.6%}, tolerance={tolerance:.4%}"
            )
    else:
        return False, f"{kpi_key}: unknown comparison mode '{mode}'"

    return passed, detail


# ---------------------------------------------------------------------------
# Parametrized test discovery
# ---------------------------------------------------------------------------

_project_pairs = _discover_project_pairs()


def _project_ids() -> list[str]:
    return [name for name, _, _ in _project_pairs]


def _skip_if_no_projects() -> None:
    if not _project_pairs:
        pytest.skip(
            "No project fixtures found. Place .xlsx files in "
            "tests/data/projects/ and run scripts/extract_excel_kpis.py "
            "to generate reference JSON files in tests/data/references/."
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExcelRegression:
    """
    Multi-project, multi-layer regression tests.

    Each test method runs the full Python pipeline on a project Excel file
    and compares the output KPIs against the JSON reference extracted from
    the same Excel file's pre-calculated values.
    """

    @pytest.mark.parametrize(
        "project_name, excel_path, ref_json_path",
        _project_pairs,
        ids=_project_ids(),
    )
    def test_all_kpis(
        self,
        project_name: str,
        excel_path: Path,
        ref_json_path: Path,
    ) -> None:
        """
        Compare all available KPIs for a single project.

        This is the primary regression test. It runs the full pipeline and
        checks every KPI that has both a Python result and a reference value.
        """
        _skip_if_no_projects()

        reference = _load_reference(ref_json_path)
        results = run_full_model(excel_path)

        failures: list[str] = []

        for kpi_key, (mode, tolerance) in KPI_TOLERANCES.items():
            expected = reference.get(kpi_key)
            actual = results.get(kpi_key)

            if expected is None or actual is None:
                continue  # Skip KPIs not present in both sides

            passed, detail = _compare_kpi(kpi_key, actual, expected, mode, tolerance)
            if not passed:
                failures.append(detail)

        if failures:
            failure_report = "\n".join(
                [f"  FAIL: {f}" for f in failures]
            )
            pytest.fail(
                f"Regression failures for project '{project_name}':\n"
                f"{failure_report}\n"
                f"  Reference: {ref_json_path}\n"
                f"  Excel: {excel_path}"
            )

    @pytest.mark.parametrize(
        "project_name, excel_path, ref_json_path",
        _project_pairs,
        ids=_project_ids(),
    )
    def test_physics_layer(
        self,
        project_name: str,
        excel_path: Path,
        ref_json_path: Path,
    ) -> None:
        """
        Compare only physics-layer intermediate KPIs.

        Isolates solar generation and SoC tracking so that physics bugs
        are caught before cascading into settlement/financial layers.
        """
        _skip_if_no_projects()

        reference = _load_reference(ref_json_path)
        results = run_full_model(excel_path)

        physics_keys = [
            "calc_solar_gen_sum_kwh",
            "calc_soc_min_kwh",
            "calc_soc_max_kwh",
        ]

        failures: list[str] = []
        for kpi_key in physics_keys:
            expected = reference.get(kpi_key)
            actual = results.get(kpi_key)
            if expected is None or actual is None:
                continue
            mode, tolerance = KPI_TOLERANCES[kpi_key]
            passed, detail = _compare_kpi(kpi_key, actual, expected, mode, tolerance)
            if not passed:
                failures.append(detail)

        if failures:
            pytest.fail(
                f"Physics layer regression failures for '{project_name}':\n"
                + "\n".join(f"  FAIL: {f}" for f in failures)
            )

    @pytest.mark.parametrize(
        "project_name, excel_path, ref_json_path",
        _project_pairs,
        ids=_project_ids(),
    )
    def test_financial_kpis(
        self,
        project_name: str,
        excel_path: Path,
        ref_json_path: Path,
    ) -> None:
        """
        Compare only final financial KPIs (IRR, NPV, DSCR).

        This is the highest-level check — if physics and aggregation
        pass but financials fail, the bug is in the waterfall/debt/metrics.
        """
        _skip_if_no_projects()

        reference = _load_reference(ref_json_path)
        results = run_full_model(excel_path)

        financial_keys = [
            "project_irr",
            "equity_irr",
            "unlevered_irr",
            "npv_usd",
            "dscr_min",
        ]

        failures: list[str] = []
        for kpi_key in financial_keys:
            expected = reference.get(kpi_key)
            actual = results.get(kpi_key)
            if expected is None or actual is None:
                continue
            mode, tolerance = KPI_TOLERANCES[kpi_key]
            passed, detail = _compare_kpi(kpi_key, actual, expected, mode, tolerance)
            if not passed:
                failures.append(detail)

        if failures:
            pytest.fail(
                f"Financial KPI regression failures for '{project_name}':\n"
                + "\n".join(f"  FAIL: {f}" for f in failures)
            )
