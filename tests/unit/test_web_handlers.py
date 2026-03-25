"""Unit tests for web function endpoint handlers."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

try:
    from flask import Flask, request
except ModuleNotFoundError:
    pytest.skip("flask is required for web handler tests", allow_module_level=True)

FUNCTIONS_DIR = Path(__file__).resolve().parents[2] / "web" / "functions"
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.append(str(FUNCTIONS_DIR))

from handlers.compare_scenarios import handle_compare_scenarios  # noqa: E402
from handlers.run_excel import handle_run_excel  # noqa: E402
from handlers.run_json import _build_project_payload, handle_run_json  # noqa: E402
from handlers.run_sensitivity import handle_run_sensitivity  # noqa: E402


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


def _extract_response_json(response: Any) -> dict[str, Any]:
    flask_response = response[0] if isinstance(response, tuple) else response
    payload = flask_response.get_json(silent=True)
    assert isinstance(payload, dict)
    return payload


def test_handle_run_excel_requires_post(app: Flask) -> None:
    with app.test_request_context("/api/run-excel", method="GET"):
        response = handle_run_excel(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    assert status == 405


def test_handle_run_excel_rejects_missing_file(app: Flask) -> None:
    with app.test_request_context("/api/run-excel", method="POST"):
        response = handle_run_excel(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "Missing required upload" in str(payload["error"])


def test_handle_run_excel_success(monkeypatch: pytest.MonkeyPatch, app: Flask) -> None:
    def fake_run_full_model(_: Path) -> dict[str, float]:
        return {
            "project_irr": 0.05,
            "npv_usd": 1000.0,
            "_annual_df": None,
        }

    monkeypatch.setattr("handlers.run_excel.run_full_model", fake_run_full_model)

    data = {
        "file": (io.BytesIO(b"dummy"), "project.xlsx"),
    }
    with app.test_request_context("/api/run-excel", method="POST", data=data):
        response = handle_run_excel(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert payload["kpis"]["project_irr"] == 0.05
    assert payload["lifetime"] == []
    assert payload["annual"] == []


def test_handle_run_json_requires_hourly_csv(app: Flask) -> None:
    with app.test_request_context("/api/run-json", method="POST"):
        response = handle_run_json(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "hourly_csv" in str(payload["error"])


def test_handle_run_json_success(monkeypatch: pytest.MonkeyPatch, app: Flask) -> None:
    def fake_run_model_from_json(_: Path) -> dict[str, Any]:
        return {
            "project_irr": 0.04,
            "_lifetime_df": None,
            "_annual_df": None,
        }

    monkeypatch.setattr("handlers.run_json.run_model_from_json", fake_run_model_from_json)

    form_data = {
        "project_name": "Test Project",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
        "degradation_json": json.dumps(
            [
                {
                    "year": 1,
                    "pv_retention": 1.0,
                    "battery_retention": 1.0,
                    "battery_with_replacement": 1.0,
                }
            ]
        ),
    }
    with app.test_request_context("/api/run-json", method="POST", data=form_data):
        response = handle_run_json(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert payload["kpis"]["project_irr"] == 0.04
    assert payload["annual"] == []


def test_handle_compare_scenarios_requires_hourly_csv(app: Flask) -> None:
    with app.test_request_context("/api/compare-scenarios", method="POST"):
        response = handle_compare_scenarios(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "hourly_csv" in str(payload["error"])


def test_handle_compare_scenarios_success(monkeypatch: pytest.MonkeyPatch, app: Flask) -> None:
    def fake_run_all_scenarios(*, project_dir: Path) -> dict[int, dict[str, Any]]:
        assert project_dir.exists()
        return {
            1: {"ppa_option": 1, "project_irr": 0.11, "ppa_label": "Bundled Discount"},
            3: {"ppa_option": 3, "project_irr": 0.08, "ppa_label": "DPPA (CfD)"},
        }

    monkeypatch.setattr("handlers.compare_scenarios.run_all_scenarios", fake_run_all_scenarios)

    form_data = {
        "project_name": "Scenario Test",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/compare-scenarios", method="POST", data=form_data):
        response = handle_compare_scenarios(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert payload["scenarios"]["1"]["project_irr"] == pytest.approx(0.11)
    assert payload["scenarios"]["3"]["ppa_label"] == "DPPA (CfD)"


def test_handle_run_sensitivity_requires_variable(app: Flask) -> None:
    form_data = {
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-sensitivity", method="POST", data=form_data):
        response = handle_run_sensitivity(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert payload["error"] == "sensitivity_variable is required"


def test_handle_run_sensitivity_success(monkeypatch: pytest.MonkeyPatch, app: Flask) -> None:
    def fake_run_sensitivity_for_values(
        *,
        variable_name: str,
        test_values: list[float],
        project_dir: Path,
        base_params: dict[str, Any],
        ppa_option: int,
    ) -> dict[float, dict[str, Any]]:
        assert variable_name == "strike_price_vnd"
        assert test_values == [1600.0, 1800.0, 2000.0]
        assert project_dir.exists()
        assert base_params["actual_capacity_kwp"] == 1000
        assert ppa_option == 3
        return {
            1600.0: {"project_irr": 0.07},
            1800.0: {"project_irr": 0.08},
            2000.0: {"project_irr": 0.09},
        }

    monkeypatch.setattr(
        "handlers.run_sensitivity.run_sensitivity_for_values",
        fake_run_sensitivity_for_values,
    )

    form_data = {
        "project_name": "Sensitivity Test",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "ppa_option": "3",
        "sensitivity_variable": "strike_price_vnd",
        "sensitivity_values": json.dumps([1600, 1800, 2000]),
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-sensitivity", method="POST", data=form_data):
        response = handle_run_sensitivity(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert payload["variable"] == "strike_price_vnd"
    assert payload["results"]["1800.0"]["project_irr"] == pytest.approx(0.08)


def test_build_project_payload_includes_all_ppa_options() -> None:
    payload = _build_project_payload(
        {
            "project_name": "PPA Test",
            "actual_capacity_kwp": "1000",
            "simulation_capacity_kwp": "100",
            "total_bess_kwh": "500",
            "bess_power_rating_kw": "250",
            "dod": "0.85",
            "half_cycle_efficiency": "0.95",
            "connection_voltage_kv": "22",
            "exchange_rate_usd_vnd": "26000",
            "project_years": "20",
            "ppa_option": "4",
            "bundled_discount_pct": "0.12",
            "pv_discount_pct": "0.07",
            "bess_discount_pct": "0.09",
            "fixed_ppa_price_usd_per_mwh": "68",
            "fixed_ppa_curtailment_pct": "0.04",
            "fixed_ppa_tx_loss_pct": "0.02",
            "revenue_escalation_pct": "0.06",
            "fmp_descent_pct": "-0.03",
        }
    )

    assert payload["ppa_settings"]["active_ppa_option"] == 4
    assert payload["ppa_settings"]["option_1_corporate_buyer"][
        "bundled_discount_to_evn_tariff_pct"
    ] == pytest.approx(0.12)
    assert payload["ppa_settings"]["option_1_corporate_buyer"][
        "evn_price_escalation_pct_pa"
    ] == pytest.approx(0.06)
    assert payload["ppa_settings"]["option_2_pv_bess_discount"][
        "pv_discount_to_evn_tariff_pct"
    ] == pytest.approx(0.07)
    assert payload["ppa_settings"]["option_2_pv_bess_discount"][
        "bess_discount_to_evn_tariff_pct"
    ] == pytest.approx(0.09)
    assert payload["ppa_settings"]["option_4_ppa_with_evn"][
        "all_in_fixed_price_USD_MWh"
    ] == pytest.approx(68.0)
    assert payload["ppa_settings"]["option_4_ppa_with_evn"]["curtailment_pct"] == pytest.approx(
        0.04
    )
    assert payload["ppa_settings"]["option_4_ppa_with_evn"][
        "transmission_loss_pct"
    ] == pytest.approx(0.02)
    assert payload["ppa_settings"]["option_3_dppa"][
        "avg_sun_hours_market_price_descent_pct_pa"
    ] == pytest.approx(-0.03)


def test_build_project_payload_includes_loader_required_financial_defaults() -> None:
    payload = _build_project_payload(
        {
            "actual_capacity_kwp": "3221",
            "simulation_capacity_kwp": "100",
            "total_bess_kwh": "2150",
            "bess_power_rating_kw": "1000",
            "project_years": "20",
            "hourly_csv": "ignored-by-builder",
        }
    )

    assert payload["capex"]["land_acquisition_USD"] == pytest.approx(0.0)
    assert payload["capex"]["bop_USD"] == pytest.approx(0.0)
    assert payload["capex"]["depreciation_tenor_years"] == 20
    assert payload["opex"]["solar_om_USD_per_MWp_pa"] == pytest.approx(6000.0)
    assert payload["financial_assumptions"]["debt_sizing"]["maximum_leverage_pct"] == pytest.approx(
        0.7
    )
    assert payload["financial_assumptions"]["return_expectations"][
        "target_minimum_equity_irr_pct"
    ] == pytest.approx(0.1)
    assert payload["financial_assumptions"]["tax"]["corporate_tax_rate_pct"] == pytest.approx(0.2)
    assert payload["retail_tariff_matrix"]["mra_buildup_assumption"] == [
        {"year": 0, "pct": 0.1},
        {"year": 1, "pct": 0.3},
        {"year": 2, "pct": 0.3},
        {"year": 3, "pct": 0.3},
    ]
