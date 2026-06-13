"""Handler for tariff-mode comparison (1-component vs 2-component).

Runs the pipeline twice via :func:`run_tariff_mode_comparison` and returns a
JSON-safe ``{"1-component", "2-component", "delta"}`` payload. The delta
highlights the demand-charge-savings vs grid-energy-savings trade-off
introduced by Vietnam's Decree 146/2025 two-component tariff.

Single-source pattern: structured form + ``hourly_csv`` (mirrors
``compare_scenarios``). Excel-upload comparison is out of scope - users
needing the Excel path can already run both modes individually via
``run_excel`` with ``tariff_mode=1-component`` / ``2-component``.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any

from flask import Request, Response, jsonify
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload
from re_storage.core.exceptions import REStorageError
from re_storage.scenarios.sensitivity import run_tariff_mode_comparison


def _sanitize(value: Any) -> Any:
    """Strip NaN/Inf so the payload survives ``jsonify``."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _serialise_mode(mode_kpis: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize(value) for key, value in mode_kpis.items() if not key.startswith("_")}


def _serialise_results(results: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {mode: _serialise_mode(kpis) for mode, kpis in results.items()}


def handle_compare_tariff_modes(request: Request) -> Response:
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
        ppa_option = int(float(form.get("ppa_option", "3")))
    except ValueError as exc:
        if isinstance(exc, json.JSONDecodeError):
            return jsonify(
                {"error": f"Invalid degradation_json: {exc}", "type": "JSONDecodeError"}
            ), 400
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        (project_dir / "project.json").write_text(json.dumps(payload), encoding="utf-8")
        uploaded_csv.save(str(project_dir / "hourly.csv"))

        try:
            results = run_tariff_mode_comparison(
                project_dir=project_dir,
                ppa_option=ppa_option,
            )
            return jsonify(_serialise_results(results))
        except REStorageError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
        except Exception as exc:  # pragma: no cover - defensive catch-all
            return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
