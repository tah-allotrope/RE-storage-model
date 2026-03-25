"""Handler for structured sensitivity-analysis runs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from flask import Request, Response, jsonify
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload
from re_storage.core.exceptions import REStorageError
from re_storage.scenarios.sensitivity import run_sensitivity_for_values


def _build_base_params(form: dict[str, str]) -> dict[str, Any]:
    base_params: dict[str, Any] = {}
    for key, raw_value in form.items():
        if key in {
            "project_name",
            "degradation_json",
            "sensitivity_variable",
            "sensitivity_values",
        }:
            continue
        if raw_value.strip() == "":
            continue
        try:
            numeric = float(raw_value)
        except ValueError:
            base_params[key] = raw_value
            continue
        base_params[key] = int(numeric) if numeric.is_integer() else numeric
    return base_params


def _parse_test_values(form: dict[str, str]) -> list[float]:
    raw = form.get("sensitivity_values", "")
    if raw.strip() == "":
        raise ValueError("sensitivity_values is required")

    parsed = json.loads(raw)
    if not isinstance(parsed, list) or len(parsed) == 0:
        raise ValueError("sensitivity_values must be a non-empty JSON array")

    values: list[float] = []
    for item in parsed:
        values.append(float(item))
    return values


def handle_run_sensitivity(request: Request) -> Response:
    method_error = ensure_post_method(request)
    if method_error is not None:
        return jsonify({"error": method_error}), 405

    file_error = ensure_uploaded_file(request, "hourly_csv")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded_csv = request.files["hourly_csv"]
    form = dict(request.form)
    variable_name = form.get("sensitivity_variable", "").strip()
    if variable_name == "":
        return jsonify({"error": "sensitivity_variable is required"}), 400

    try:
        payload = build_project_payload(form)
        test_values = _parse_test_values(form)
        ppa_option = int(float(form.get("ppa_option", "3")))
    except ValueError as exc:
        if isinstance(exc, json.JSONDecodeError):
            return jsonify({"error": f"Invalid JSON field: {exc}", "type": "JSONDecodeError"}), 400
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        json_path = project_dir / "project.json"
        csv_path = project_dir / "hourly.csv"

        json_path.write_text(json.dumps(payload), encoding="utf-8")
        uploaded_csv.save(str(csv_path))

        try:
            sensitivity_results = run_sensitivity_for_values(
                variable_name=variable_name,
                test_values=test_values,
                project_dir=project_dir,
                base_params=_build_base_params(form),
                ppa_option=ppa_option,
            )
            return jsonify(
                {
                    "variable": variable_name,
                    "results": {
                        str(value): dict(payload) for value, payload in sensitivity_results.items()
                    },
                }
            )
        except REStorageError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
