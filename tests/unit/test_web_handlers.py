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

from handlers.run_excel import handle_run_excel  # noqa: E402
from handlers.run_json import handle_run_json  # noqa: E402


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
        return {"project_irr": 0.05, "npv_usd": 1000.0}

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
