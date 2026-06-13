"""Handler for scenario comparison runs across PPA options."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from flask import Request, Response, jsonify
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload, resolve_tariff_mode
from re_storage.core.exceptions import REStorageError
from re_storage.scenarios.runner import run_all_scenarios


def _serialise_scenario_results(
    results: dict[int, dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {str(option): dict(payload) for option, payload in results.items()}


def handle_compare_scenarios(request: Request) -> Response:
    method_error = ensure_post_method(request)
    if method_error is not None:
        return jsonify({"error": method_error}), 405

    file_error = ensure_uploaded_file(request, "hourly_csv")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded_csv = request.files["hourly_csv"]
    form = dict(request.form)

    try:
        payload = build_project_payload(form)
        tariff_mode = resolve_tariff_mode(form)
    except ValueError as exc:
        if isinstance(exc, json.JSONDecodeError):
            return jsonify(
                {"error": f"Invalid degradation_json: {exc}", "type": "JSONDecodeError"}
            ), 400
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        json_path = project_dir / "project.json"
        csv_path = project_dir / "hourly.csv"

        json_path.write_text(json.dumps(payload), encoding="utf-8")
        uploaded_csv.save(str(csv_path))

        try:
            scenario_results = run_all_scenarios(
                project_dir=project_dir,
                tariff_mode=tariff_mode,
            )
            return jsonify({"scenarios": _serialise_scenario_results(scenario_results)})
        except REStorageError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
