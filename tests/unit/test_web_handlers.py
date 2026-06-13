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
from handlers.compare_tariff_modes import handle_compare_tariff_modes  # noqa: E402
from handlers.export_workbook import handle_export_workbook  # noqa: E402
from handlers.run_excel import handle_run_excel  # noqa: E402
from handlers.run_json import _build_project_payload, handle_run_json  # noqa: E402
from handlers.run_report import handle_run_report  # noqa: E402
from handlers.run_sensitivity import handle_run_sensitivity  # noqa: E402
from utils.serialise import serialise_results  # noqa: E402


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
    def fake_run_full_model(_: Path, **_kwargs: Any) -> dict[str, float]:
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
    def fake_run_model_from_json(_: Path, **_kwargs: Any) -> dict[str, Any]:
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
    def fake_run_all_scenarios(*, project_dir: Path, **_kwargs: Any) -> dict[int, dict[str, Any]]:
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
        **_kwargs: Any,
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


def test_serialise_results_includes_go_verdict() -> None:
    results = {
        "equity_irr": 0.15,
        "dscr_min": 1.4,
        "npv_usd": 2_000_000.0,
        "simple_payback_years": 9.0,
    }

    payload = serialise_results(results)
    verdict = payload["verdict"]

    assert verdict["overall"] == "GO"
    assert verdict["equity_irr_status"] == "PASS"
    assert verdict["dscr_status"] == "PASS"
    assert verdict["npv_status"] == "PASS"
    assert verdict["payback_status"] == "PASS"
    assert isinstance(verdict["details"], list)
    assert len(verdict["details"]) == 4


def test_serialise_results_no_go_verdict_on_failures() -> None:
    results = {
        "equity_irr": 0.02,
        "dscr_min": 0.9,
        "npv_usd": -5_000_000.0,
        "simple_payback_years": 30.0,
    }

    payload = serialise_results(results)

    assert payload["verdict"]["overall"] == "NO-GO"


def test_serialise_results_verdict_handles_missing_payback() -> None:
    results = {
        "equity_irr": 0.15,
        "dscr_min": 1.4,
        "npv_usd": 2_000_000.0,
        "simple_payback_years": None,
    }

    payload = serialise_results(results)

    # Missing payback degrades to FAIL rather than raising.
    assert payload["verdict"]["payback_status"] == "FAIL"
    assert payload["verdict"]["overall"] == "NO-GO"


def test_serialise_results_accepts_threshold_override() -> None:
    from re_storage.reporting.assessment import AssessmentThresholds

    results = {
        "equity_irr": 0.15,
        "dscr_min": 1.25,
        "npv_usd": 2_000_000.0,
        "simple_payback_years": 9.0,
    }

    # Default covenant (1.2): DSCR 1.25 passes.
    assert serialise_results(results)["verdict"]["dscr_status"] == "PASS"

    # Stricter covenant (1.5): DSCR 1.25 fails, dragging the verdict to NO-GO.
    strict = serialise_results(results, thresholds=AssessmentThresholds(dscr_covenant=1.5))
    assert strict["verdict"]["dscr_status"] == "FAIL"
    assert strict["verdict"]["overall"] == "NO-GO"


def test_run_excel_success_response_carries_verdict(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    def fake_run_full_model(_: Path, **_kwargs: Any) -> dict[str, float]:
        return {
            "equity_irr": 0.15,
            "dscr_min": 1.4,
            "npv_usd": 2_000_000.0,
            "simple_payback_years": 9.0,
        }

    monkeypatch.setattr("handlers.run_excel.run_full_model", fake_run_full_model)

    data = {"file": (io.BytesIO(b"dummy"), "project.xlsx")}
    with app.test_request_context("/api/run-excel", method="POST", data=data):
        response = handle_run_excel(request)

    payload = _extract_response_json(response)
    assert payload["verdict"]["overall"] == "GO"


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


def test_handle_run_report_requires_post(app: Flask) -> None:
    with app.test_request_context("/api/run-report", method="GET"):
        response = handle_run_report(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    assert status == 405


def test_handle_run_report_json_path_returns_html(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    def fake_run_model_from_json(_: Path, **_kwargs: Any) -> dict[str, Any]:
        return {
            "project_irr": 0.08,
            "_lifetime_df": "lifetime-sentinel",
            "_hourly_df": "hourly-sentinel",
        }

    captured: dict[str, Any] = {}

    def fake_generate_report(
        project_config: dict[str, Any],
        model_results: dict[str, Any],
        reference_kpis: Any,
        lifetime_df: Any,
        hourly_df: Any,
    ) -> str:
        captured["project_config"] = project_config
        captured["model_results"] = model_results
        captured["reference_kpis"] = reference_kpis
        captured["lifetime_df"] = lifetime_df
        captured["hourly_df"] = hourly_df
        return "<html><body>RE-Storage Report</body></html>"

    monkeypatch.setattr("handlers.run_report.run_model_from_json", fake_run_model_from_json)
    monkeypatch.setattr("handlers.run_report.generate_report", fake_generate_report)

    form_data = {
        "project_name": "Test Report Project",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-report", method="POST", data=form_data):
        response = handle_run_report(request)

    flask_response = response[0] if isinstance(response, tuple) else response
    status = response[1] if isinstance(response, tuple) else flask_response.status_code

    assert status == 200
    assert flask_response.mimetype == "text/html"
    assert "attachment" in flask_response.headers["Content-Disposition"]
    assert "test-report-project" in flask_response.headers["Content-Disposition"]
    assert flask_response.headers["Access-Control-Expose-Headers"] == "Content-Disposition"
    assert b"RE-Storage Report" in flask_response.get_data()

    assert captured["reference_kpis"] is None
    assert captured["lifetime_df"] == "lifetime-sentinel"
    assert captured["hourly_df"] == "hourly-sentinel"
    assert "_lifetime_df" not in captured["model_results"]
    assert captured["model_results"]["project_irr"] == 0.08
    assert "system_input" in captured["project_config"]


def test_handle_run_report_json_path_requires_hourly_csv(app: Flask) -> None:
    with app.test_request_context("/api/run-report", method="POST", data={}):
        response = handle_run_report(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "hourly_csv" in str(payload["error"])


def test_handle_run_report_excel_path_returns_html(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    def fake_run_full_model(_: Path, **_kwargs: Any) -> dict[str, Any]:
        return {
            "project_irr": 0.07,
            "_lifetime_df": "lifetime-sentinel",
            "_hourly_df": "hourly-sentinel",
        }

    def fake_generate_report(**_: Any) -> str:
        return "<html>Excel Report</html>"

    monkeypatch.setattr("handlers.run_report.run_full_model", fake_run_full_model)
    monkeypatch.setattr("handlers.run_report.generate_report", fake_generate_report)

    data = {
        "source": "excel",
        "file": (io.BytesIO(b"dummy"), "project.xlsx"),
    }
    with app.test_request_context("/api/run-report", method="POST", data=data):
        response = handle_run_report(request)

    flask_response = response[0] if isinstance(response, tuple) else response
    status = response[1] if isinstance(response, tuple) else flask_response.status_code

    assert status == 200
    assert flask_response.mimetype == "text/html"
    assert b"Excel Report" in flask_response.get_data()


def test_handle_run_report_excel_path_requires_file(app: Flask) -> None:
    with app.test_request_context(
        "/api/run-report", method="POST", data={"source": "excel"}
    ):
        response = handle_run_report(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "file" in str(payload["error"])


def test_handle_run_report_excel_path_rejects_non_xlsx(app: Flask) -> None:
    data = {
        "source": "excel",
        "file": (io.BytesIO(b"dummy"), "project.csv"),
    }
    with app.test_request_context("/api/run-report", method="POST", data=data):
        response = handle_run_report(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert ".xlsx" in str(payload["error"])


def test_handle_run_report_missing_dataframes_returns_422(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    def fake_run_model_from_json(_: Path, **_kwargs: Any) -> dict[str, Any]:
        return {"project_irr": 0.04, "_lifetime_df": None, "_hourly_df": None}

    monkeypatch.setattr("handlers.run_report.run_model_from_json", fake_run_model_from_json)

    form_data = {
        "project_name": "No DataFrames",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-report", method="POST", data=form_data):
        response = handle_run_report(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 422
    assert "lifetime" in str(payload["error"]).lower() or "hourly" in str(payload["error"]).lower()


# ---------------------------------------------------------------------------
# Excel workbook export (GAP-02 PHASE-02)
# ---------------------------------------------------------------------------


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _kpis_for_workbook() -> dict[str, Any]:
    return {
        "project_irr": 0.09,
        "equity_irr": 0.14,
        "npv_usd": 1_500_000.0,
        "dscr_min": 1.35,
        "dscr_avg": 1.55,
        "simple_payback_years": 8.5,
        "year1_solar_generation_mwh": 5500.0,
        "year1_dppa_revenue_usd": 320_000.0,
        "year1_grid_savings_usd": 180_000.0,
        "year1_opex_usd": 90_000.0,
        "year1_ebitda_usd": 410_000.0,
        "debt_amount_usd": 12_000_000.0,
        "exchange_rate_usd_vnd": 26_000.0,
        "bess_power_rating_kw": 1_000.0,
        "actual_capacity_kwp": 3_221.0,
    }


def test_handle_export_workbook_requires_post(app: Flask) -> None:
    with app.test_request_context("/api/export-workbook", method="GET"):
        response = handle_export_workbook(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    assert status == 405


def test_handle_export_workbook_json_path_returns_xlsx(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    import pandas as pd

    annual_df = pd.DataFrame(
        {
            "year": [1, 2],
            "dppa_revenue_usd": [320_000.0, 330_000.0],
            "ebitda_usd": [410_000.0, 420_000.0],
            "cfads_usd": [400_000.0, 410_000.0],
            "dscr": [1.35, 1.40],
        }
    )

    def fake_run_model_from_json(_: Path, **_kwargs: Any) -> dict[str, Any]:
        results = _kpis_for_workbook()
        results["_annual_df"] = annual_df
        return results

    monkeypatch.setattr(
        "handlers.export_workbook.run_model_from_json", fake_run_model_from_json
    )

    form_data = {
        "project_name": "Workbook Test Project",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/export-workbook", method="POST", data=form_data):
        response = handle_export_workbook(request)

    flask_response = response[0] if isinstance(response, tuple) else response
    status = response[1] if isinstance(response, tuple) else flask_response.status_code

    assert status == 200
    assert flask_response.mimetype == _XLSX_MIME
    assert "attachment" in flask_response.headers["Content-Disposition"]
    assert "workbook-test-project" in flask_response.headers["Content-Disposition"]
    assert flask_response.headers["Access-Control-Expose-Headers"] == "Content-Disposition"

    body = flask_response.get_data()
    assert body[:2] == b"PK"  # xlsx is a zip

    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(body))
    sheet_names = wb.sheetnames
    assert "Cover" in sheet_names
    assert "Assumptions" in sheet_names
    assert any(name.startswith("Assessment") for name in sheet_names)
    # Single-run scope: no Comparison / Sensitivity sheets.
    assert not any(name.startswith("Comparison") for name in sheet_names)
    assert "Sensitivity" not in sheet_names


def test_handle_export_workbook_json_path_requires_hourly_csv(app: Flask) -> None:
    with app.test_request_context("/api/export-workbook", method="POST", data={}):
        response = handle_export_workbook(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "hourly_csv" in str(payload["error"])


def test_handle_export_workbook_excel_path_returns_xlsx(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    import pandas as pd

    annual_df = pd.DataFrame(
        {
            "year": [1],
            "dppa_revenue_usd": [320_000.0],
            "ebitda_usd": [410_000.0],
            "cfads_usd": [400_000.0],
            "dscr": [1.35],
        }
    )

    def fake_run_full_model(_: Path, **_kwargs: Any) -> dict[str, Any]:
        results = _kpis_for_workbook()
        results["_annual_df"] = annual_df
        return results

    monkeypatch.setattr("handlers.export_workbook.run_full_model", fake_run_full_model)

    data = {
        "source": "excel",
        "file": (io.BytesIO(b"dummy"), "project.xlsx"),
    }
    with app.test_request_context("/api/export-workbook", method="POST", data=data):
        response = handle_export_workbook(request)

    flask_response = response[0] if isinstance(response, tuple) else response
    status = response[1] if isinstance(response, tuple) else flask_response.status_code

    assert status == 200
    assert flask_response.mimetype == _XLSX_MIME
    body = flask_response.get_data()
    assert body[:2] == b"PK"


def test_handle_export_workbook_excel_path_requires_file(app: Flask) -> None:
    with app.test_request_context(
        "/api/export-workbook", method="POST", data={"source": "excel"}
    ):
        response = handle_export_workbook(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "file" in str(payload["error"])


def test_handle_export_workbook_excel_path_rejects_non_xlsx(app: Flask) -> None:
    data = {
        "source": "excel",
        "file": (io.BytesIO(b"dummy"), "project.csv"),
    }
    with app.test_request_context("/api/export-workbook", method="POST", data=data):
        response = handle_export_workbook(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert ".xlsx" in str(payload["error"])


# ---------------------------------------------------------------------------
# Two-component tariff (GAP-03 PHASE-01)
# ---------------------------------------------------------------------------


def test_build_project_payload_defaults_to_one_component() -> None:
    payload = _build_project_payload(
        {
            "actual_capacity_kwp": "1000",
            "simulation_capacity_kwp": "100",
        }
    )

    tariff = payload["grid_connection_and_tariff"]
    assert tariff["tariff_structure"] == "1-component"
    assert tariff["evn_retail_tariff_VND"]["Cp_demand"] == pytest.approx(0.0)


def test_build_project_payload_threads_two_component_tariff_mode() -> None:
    payload = _build_project_payload(
        {
            "actual_capacity_kwp": "1000",
            "simulation_capacity_kwp": "100",
            "tariff_mode": "2-component",
            "cp_demand_vnd_per_kw": "15000",
            "evn_tariff_standard_vnd": "1900",
            "evn_tariff_peak_vnd": "3500",
            "evn_tariff_off_peak_vnd": "1100",
        }
    )

    tariff = payload["grid_connection_and_tariff"]
    assert tariff["tariff_structure"] == "2-component"
    assert tariff["evn_retail_tariff_VND"]["Cp_demand"] == pytest.approx(15000.0)
    assert tariff["evn_retail_tariff_VND"]["Ca_normal"] == pytest.approx(1900.0)
    assert tariff["evn_retail_tariff_VND"]["Ca_peak"] == pytest.approx(3500.0)
    assert tariff["evn_retail_tariff_VND"]["Ca_offpeak"] == pytest.approx(1100.0)


def test_build_project_payload_rejects_invalid_tariff_mode() -> None:
    with pytest.raises(ValueError, match="tariff_mode"):
        _build_project_payload(
            {
                "actual_capacity_kwp": "1000",
                "simulation_capacity_kwp": "100",
                "tariff_mode": "3-component",
            }
        )


def test_handle_run_json_passes_tariff_mode_to_pipeline(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    captured: dict[str, Any] = {}

    def fake_run_model_from_json(project_dir: Path, **kwargs: Any) -> dict[str, Any]:
        captured["project_dir"] = project_dir
        captured["kwargs"] = kwargs
        mode = kwargs.get("tariff_mode", "1-component")
        return {
            "project_irr": 0.07,
            "tariff_mode": mode,
            "demand_charge_savings_usd": 8_000.0 if mode == "2-component" else 0.0,
            "_annual_df": None,
            "_lifetime_df": None,
        }

    monkeypatch.setattr("handlers.run_json.run_model_from_json", fake_run_model_from_json)

    form_data = {
        "project_name": "2C Test",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "tariff_mode": "2-component",
        "cp_demand_vnd_per_kw": "12000",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-json", method="POST", data=form_data):
        response = handle_run_json(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert captured["kwargs"].get("tariff_mode") == "2-component"
    assert payload["kpis"]["tariff_mode"] == "2-component"
    assert payload["kpis"]["demand_charge_savings_usd"] == pytest.approx(8000.0)


def test_handle_run_json_rejects_invalid_tariff_mode(app: Flask) -> None:
    form_data = {
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "tariff_mode": "nonsense",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context("/api/run-json", method="POST", data=form_data):
        response = handle_run_json(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "tariff_mode" in str(payload["error"])


# ---------------------------------------------------------------------------
# Tariff-mode comparison (GAP-03 PHASE-03)
# ---------------------------------------------------------------------------


def test_handle_compare_tariff_modes_requires_post(app: Flask) -> None:
    with app.test_request_context("/api/compare-tariff-modes", method="GET"):
        response = handle_compare_tariff_modes(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    assert status == 405


def test_handle_compare_tariff_modes_requires_hourly_csv(app: Flask) -> None:
    with app.test_request_context("/api/compare-tariff-modes", method="POST", data={}):
        response = handle_compare_tariff_modes(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 400
    assert "hourly_csv" in str(payload["error"])


def test_handle_compare_tariff_modes_success(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    def fake_run_tariff_mode_comparison(
        *,
        project_dir: Path,
        ppa_option: int,
        **_kwargs: Any,
    ) -> dict[str, dict[str, Any]]:
        assert project_dir.exists()
        assert ppa_option == 3
        return {
            "1-component": {
                "project_irr": 0.08,
                "year1_grid_savings_usd": 303_900.0,
                "demand_charge_savings_usd": 0.0,
            },
            "2-component": {
                "project_irr": 0.075,
                "year1_grid_savings_usd": 203_100.0,
                "demand_charge_savings_usd": 8_000.0,
            },
            "delta": {
                "project_irr": -0.005,
                "year1_grid_savings_usd": -100_800.0,
                "demand_charge_savings_usd": 8_000.0,
            },
        }

    monkeypatch.setattr(
        "handlers.compare_tariff_modes.run_tariff_mode_comparison",
        fake_run_tariff_mode_comparison,
    )

    form_data = {
        "project_name": "Tariff Comparison Test",
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "ppa_option": "3",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context(
        "/api/compare-tariff-modes", method="POST", data=form_data
    ):
        response = handle_compare_tariff_modes(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    assert set(payload.keys()) >= {"1-component", "2-component", "delta"}
    assert payload["1-component"]["year1_grid_savings_usd"] == pytest.approx(303_900.0)
    assert payload["2-component"]["demand_charge_savings_usd"] == pytest.approx(8_000.0)
    assert payload["delta"]["demand_charge_savings_usd"] == pytest.approx(8_000.0)


def test_handle_compare_tariff_modes_sanitises_nan(
    monkeypatch: pytest.MonkeyPatch, app: Flask
) -> None:
    import math

    def fake_run_tariff_mode_comparison(**_kwargs: Any) -> dict[str, dict[str, Any]]:
        return {
            "1-component": {"project_irr": 0.08, "broken": math.nan},
            "2-component": {"error": "voltage tier missing"},
            "delta": {},
        }

    monkeypatch.setattr(
        "handlers.compare_tariff_modes.run_tariff_mode_comparison",
        fake_run_tariff_mode_comparison,
    )

    form_data = {
        "actual_capacity_kwp": "1000",
        "simulation_capacity_kwp": "100",
        "hourly_csv": (
            io.BytesIO(b"datetime,SimulationProfile_kW,Irradiation_W/m2,Load_kW,FMP,CFMP\n"),
            "hourly.csv",
        ),
    }
    with app.test_request_context(
        "/api/compare-tariff-modes", method="POST", data=form_data
    ):
        response = handle_compare_tariff_modes(request)

    status = response[1] if isinstance(response, tuple) else response.status_code
    payload = _extract_response_json(response)

    assert status == 200
    # NaN must be sanitised to None for valid JSON; error string must pass through.
    assert payload["1-component"]["broken"] is None
    assert payload["2-component"]["error"] == "voltage tier missing"
