"""Handler for structured JSON+CSV model runs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from flask import Request, jsonify
from utils.serialise import serialise_results
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload, resolve_tariff_mode, to_float
from re_storage.core.exceptions import REStorageError
from re_storage.pipeline import run_model_from_json


def _build_project_payload(form: dict[str, str]):
    return build_project_payload(form)


def handle_run_json(request: Request):
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
        cp_demand_raw = form.get("cp_demand_vnd_per_kw", "").strip()
        cp_demand_vnd = to_float(form, "cp_demand_vnd_per_kw", 0.0) if cp_demand_raw else None
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
            model_results = run_model_from_json(
                project_dir,
                tariff_mode=tariff_mode,
                cp_demand_vnd_per_kw=cp_demand_vnd,
            )
            return jsonify(serialise_results(model_results))
        except REStorageError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
