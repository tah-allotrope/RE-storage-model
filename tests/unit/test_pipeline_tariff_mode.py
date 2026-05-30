"""Unit tests for the two-component tariff_mode pipeline parameter (Sprint 4 PHASE-01)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from re_storage.core.types import TimePeriod
from re_storage.pipeline import run_model_from_json

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

# Two-component pilot rates at 22 kV (Decree 146/2025), VND.
CP_DEMAND_22KV_VND = 235_414.0
CA_RATES_22KV_VND = {
    TimePeriod.OFF_PEAK: 859.0,
    TimePeriod.STANDARD: 1275.0,
    TimePeriod.PEAK: 2182.0,
}


def _ca_rates_usd(exchange_rate: float = 26_000.0) -> dict[TimePeriod, float]:
    return {period: vnd / exchange_rate for period, vnd in CA_RATES_22KV_VND.items()}


def test_invalid_tariff_mode_raises(project_dir: Path) -> None:
    """ValueError for an unsupported tariff_mode string."""
    with pytest.raises(ValueError, match="tariff_mode"):
        run_model_from_json(project_dir, tariff_mode="3-component")


def test_1component_default_no_demand_savings(project_dir: Path) -> None:
    """Default mode (1-component) yields zero demand-charge savings."""
    results = run_model_from_json(project_dir)

    assert results["tariff_mode"] == "1-component"
    assert results["demand_charge_savings_usd"] == pytest.approx(0.0)


def test_2component_activates_demand_savings(project_dir: Path) -> None:
    """2-component mode with a positive Cp returns positive demand-charge savings."""
    results = run_model_from_json(
        project_dir,
        tariff_mode="2-component",
        cp_demand_vnd_per_kw=CP_DEMAND_22KV_VND,
    )

    assert results["tariff_mode"] == "2-component"
    assert results["demand_charge_savings_usd"] > 0.0


def test_2component_lowers_energy_rates(project_dir: Path) -> None:
    """Supplying lower Ca energy rates changes Year-1 grid savings vs 1-component."""
    base = run_model_from_json(project_dir)
    two_component = run_model_from_json(
        project_dir,
        tariff_mode="2-component",
        cp_demand_vnd_per_kw=CP_DEMAND_22KV_VND,
        ca_tariff_rates=_ca_rates_usd(),
    )

    # Ca energy rates are materially lower than the 1-component EVN rates,
    # so the factory's grid energy savings differ between the two modes.
    assert two_component["year1_grid_savings_usd"] != pytest.approx(
        base["year1_grid_savings_usd"]
    )
