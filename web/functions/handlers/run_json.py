"""Handler for structured JSON+CSV model runs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from flask import Request, Response, jsonify
from utils.serialise import serialise_results
from utils.validate import ensure_post_method, ensure_uploaded_file

from re_storage.core.exceptions import REStorageError
from re_storage.pipeline import run_model_from_json


def _to_float(form: dict[str, str], key: str, default: float) -> float:
    raw = form.get(key)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _to_int(form: dict[str, str], key: str, default: int) -> int:
    raw = form.get(key)
    if raw is None or raw.strip() == "":
        return default
    return int(float(raw))


def _to_bool(form: dict[str, str], key: str, default: bool) -> bool:
    raw = form.get(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _build_project_payload(form: dict[str, str]) -> dict[str, Any]:
    actual_capacity_kwp = _to_float(form, "actual_capacity_kwp", 0.0)
    simulation_capacity_kwp = _to_float(form, "simulation_capacity_kwp", actual_capacity_kwp)
    total_bess_kwh = _to_float(form, "total_bess_kwh", 0.0)
    half_cycle_efficiency = _to_float(form, "half_cycle_efficiency", 0.95)
    connection_voltage_kv = _to_float(form, "connection_voltage_kv", 22.0)
    exchange_rate = _to_float(form, "exchange_rate_usd_vnd", 26000.0)
    strike_price_vnd = _to_float(form, "strike_price_vnd", 1800.0)
    kpp_22 = _to_float(form, "kpp_22", 1.027263)
    kpp_110 = _to_float(form, "kpp_110", 1.008525)
    project_years = _to_int(form, "project_years", 20)

    degradation_json = form.get("degradation_json", "")
    if degradation_json.strip() == "":
        annual_table = [
            {
                "year": year,
                "pv_retention": max(1.0 - 0.005 * (year - 1), 0.8),
                "battery_retention": max(1.0 - 0.02 * (year - 1), 0.5),
                "battery_with_replacement": max(1.0 - 0.015 * (year - 1), 0.6),
            }
            for year in range(1, project_years + 1)
        ]
    else:
        parsed = json.loads(degradation_json)
        if not isinstance(parsed, list):
            raise ValueError("degradation_json must be a JSON array")
        annual_table = parsed

    return {
        "project": form.get("project_name", "Web Project"),
        "model": "Solar + BESS Techno-Economic Model",
        "developer": "RE-Storage Web Tool",
        "system_input": {
            "actual_installation_capacity_kWp": actual_capacity_kwp,
            "simulation_capacity_kWp": simulation_capacity_kwp,
            "bess_included": _to_bool(form, "bess_enabled", True),
        },
        "bess_parameters": {
            "total_bess_storage_capacity_kWh": total_bess_kwh,
            "total_bess_power_output_kW": _to_float(form, "bess_power_rating_kw", 0.0),
            "depth_of_discharge_pct": _to_float(form, "dod", 0.85),
            "half_cycle_efficiency_pct": half_cycle_efficiency,
        },
        "bess_operation_strategy": {
            "strategy_mode": _to_int(form, "strategy_mode", 1),
            "charge": {
                "solar_active_charging": {
                    "pv2bess_pre_charge_mode": _to_int(form, "charging_mode", 1),
                    "pre_charge_share_of_pv_1_pct": _to_float(form, "active_pv2bess_share", 0.3),
                    "pre_charge_start_hour_1": _to_int(form, "charge_start_hour", 10),
                    "pre_charge_end_hour_1": _to_int(form, "charge_end_hour", 16),
                    "min_pv_directly_to_load_pct": _to_float(form, "min_direct_pv_share", 0.1),
                    "precharge_target_soc_kWh_2": _to_float(
                        form,
                        "precharge_target_soc_kwh",
                        max(total_bess_kwh * _to_float(form, "dod", 0.85), 0.0),
                    ),
                    "precharge_target_hour_2": _to_int(form, "precharge_target_hour", 17),
                }
            },
        },
        "financial_input": {
            "exchange_rate_USD_VND": exchange_rate,
            "timing": {
                "financial_close_excel_serial": _to_int(form, "financial_close_serial", 46022),
                "commercial_operation_date_excel_serial": _to_int(form, "cod_excel_serial", 46023),
                "project_lifetime_years": project_years,
            },
        },
        "grid_connection_and_tariff": {
            "connection_voltage_level_kV": connection_voltage_kv,
            "current_applied_evn_tariff_USD_MWh": {
                "off_peak": _to_float(form, "tariff_off_peak", 45.7692307692308),
                "standard": _to_float(form, "tariff_standard", 70.5),
                "peak": _to_float(form, "tariff_peak", 130.692307692308),
                "capacity": 0.0,
            },
        },
        "ppa_settings": {
            "option_3_dppa": {
                "model_active": _to_bool(form, "dppa_enabled", True),
                "strike_price_VND": strike_price_vnd,
                "regulation_parameters": {
                    "k": _to_float(form, "k_factor", 1.02),
                    "Kpp_22kv": kpp_22,
                    "Kpp_110kv": kpp_110,
                },
            }
        },
        "capex": {
            "solar_USD_per_MWp": _to_float(form, "solar_usd_per_mwp", 0.0),
            "bess_USD_per_MWh": _to_float(form, "bess_usd_per_mwh", 0.0),
        },
        "financial_assumptions": {
            "debt_sizing": {
                "maximum_debt_tenor_years": _to_int(form, "tenor_years", 15),
                "target_dscr_x": _to_float(form, "target_dscr", 1.3),
            },
            "interest_rate": {
                "base_rate_floating": _to_float(form, "base_rate", 0.06),
                "debt_margin_pct": _to_float(form, "debt_margin", 0.0),
            },
        },
        "degradation_and_loss": {
            "annual_table": annual_table,
        },
    }


def handle_run_json(request: Request) -> Response:
    method_error = ensure_post_method(request)
    if method_error is not None:
        return jsonify({"error": method_error}), 405

    file_error = ensure_uploaded_file(request, "hourly_csv")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded_csv = request.files["hourly_csv"]

    form = dict(request.form)

    try:
        payload = _build_project_payload(form)
    except ValueError as exc:
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
    except json.JSONDecodeError as exc:
        return jsonify(
            {"error": f"Invalid degradation_json: {exc}", "type": "JSONDecodeError"}
        ), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        json_path = project_dir / "project.json"
        csv_path = project_dir / "hourly.csv"

        json_path.write_text(json.dumps(payload), encoding="utf-8")
        uploaded_csv.save(str(csv_path))

        try:
            model_results = run_model_from_json(project_dir)
            return jsonify(serialise_results(model_results))
        except REStorageError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
