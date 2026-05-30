"""Unit tests for Sprint 4 PHASE-03 — tariff_mode in scenarios, sensitivity, and workbook."""

from __future__ import annotations

import shutil
from pathlib import Path

import openpyxl
import pytest

from re_storage.reporting.excel_writer import create_workbook, write_comparison_sheet
from re_storage.scenarios.runner import run_all_scenarios
from re_storage.scenarios.sensitivity import run_tariff_mode_comparison

EMIVEST_DIR = Path(__file__).resolve().parents[1] / "data" / "projects" / "emivest"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Isolated project dir holding exactly one JSON + one CSV (Emivest base case)."""
    shutil.copy(EMIVEST_DIR / "Emivest.json", tmp_path / "Emivest.json")
    shutil.copy(
        EMIVEST_DIR / "Emivest additional data.csv",
        tmp_path / "Emivest additional data.csv",
    )
    return tmp_path


def test_run_all_scenarios_forwards_tariff_mode(project_dir: Path) -> None:
    """run_all_scenarios threads tariff_mode through to the pipeline."""
    results = run_all_scenarios(
        project_dir=project_dir,
        ppa_options=[3],
        tariff_mode="2-component",
    )
    assert results[3]["tariff_mode"] == "2-component"
    assert results[3]["demand_charge_savings_usd"] > 0.0


def test_run_tariff_mode_comparison_returns_both_modes(project_dir: Path) -> None:
    """Categorical comparison runs both modes and reports the delta."""
    comparison = run_tariff_mode_comparison(project_dir=project_dir, ppa_option=3)

    assert set(comparison) >= {"1-component", "2-component", "delta"}
    assert comparison["1-component"]["demand_charge_savings_usd"] == pytest.approx(0.0)
    assert comparison["2-component"]["demand_charge_savings_usd"] > 0.0
    # delta carries the demand-charge swing between modes
    assert comparison["delta"]["demand_charge_savings_usd"] > 0.0


def test_comparison_sheet_renders_demand_charge_row() -> None:
    """write_comparison_sheet includes a demand-charge savings row."""
    wb = create_workbook()
    scenario_results = {
        3: {
            "project_irr": 0.12,
            "npv_usd": 1_000_000.0,
            "demand_charge_savings_usd": 8_013.54,
            "tariff_mode": "2-component",
        }
    }
    write_comparison_sheet(wb, scenario_results=scenario_results)

    ws = wb["Comparison"]
    labels = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
    assert any(label and "Demand Charge" in str(label) for label in labels)
