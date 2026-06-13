"""Handler for HTML report downloads.

Re-runs the model from posted inputs (no caching - stateless function) and
returns the polished, self-contained HTML report from
``re_storage.reporting.html_report.generate_report``.

Supports two input sources, selected via the ``source`` form field:
- ``json`` (default): structured form + ``hourly_csv`` upload (mirrors
  ``run_json``).
- ``excel``: a single ``.xlsx`` upload (mirrors ``run_excel``).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from flask import Request, Response, jsonify
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload, resolve_tariff_mode, to_float
from re_storage.core.exceptions import REStorageError
from re_storage.pipeline import run_full_model, run_model_from_json
from re_storage.reporting.html_report import generate_report

_HTML_HEADERS = {
    "Content-Type": "text/html; charset=utf-8",
    "Access-Control-Expose-Headers": "Content-Disposition",
}


def _slugify(value: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in value.lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "project"


def _filename(project_name: str | None) -> str:
    base = _slugify((project_name or "").strip())
    return f"re-storage-report-{base}.html"


def _html_response(html: str, project_name: str | None) -> Response:
    headers = dict(_HTML_HEADERS)
    headers["Content-Disposition"] = f'attachment; filename="{_filename(project_name)}"'
    return Response(html, status=200, headers=headers)


def _render_html(project_config: dict[str, Any], results: dict[str, Any]) -> str:
    lifetime_df = results.get("_lifetime_df")
    hourly_df = results.get("_hourly_df")
    if lifetime_df is None or hourly_df is None:
        raise REStorageError(
            "Model run did not produce lifetime/hourly dataframes required for the report"
        )
    model_results = {key: value for key, value in results.items() if not key.startswith("_")}
    return generate_report(
        project_config=project_config,
        model_results=model_results,
        reference_kpis=None,
        lifetime_df=lifetime_df,
        hourly_df=hourly_df,
    )


def _resolve_tariff_kwargs(form: dict[str, str]) -> dict[str, object]:
    tariff_mode = resolve_tariff_mode(form)
    cp_demand_raw = form.get("cp_demand_vnd_per_kw", "").strip()
    cp_demand_vnd: float | None = (
        to_float(form, "cp_demand_vnd_per_kw", 0.0) if cp_demand_raw else None
    )
    return {"tariff_mode": tariff_mode, "cp_demand_vnd_per_kw": cp_demand_vnd}


def _handle_json_source(request: Request, form: dict[str, str]) -> Response:
    file_error = ensure_uploaded_file(request, "hourly_csv")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded_csv = request.files["hourly_csv"]
    payload = build_project_payload(form)
    tariff_kwargs = _resolve_tariff_kwargs(form)

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        (project_dir / "project.json").write_text(json.dumps(payload), encoding="utf-8")
        uploaded_csv.save(str(project_dir / "hourly.csv"))

        results = run_model_from_json(project_dir, **tariff_kwargs)
        html = _render_html(payload, results)
        return _html_response(html, form.get("project_name"))


def _handle_excel_source(request: Request, form: dict[str, str]) -> Response:
    file_error = ensure_uploaded_file(request, "file")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded = request.files["file"]
    filename = uploaded.filename or ""
    if not filename.lower().endswith(".xlsx"):
        return jsonify({"error": "Uploaded file must have .xlsx extension"}), 400

    tariff_kwargs = _resolve_tariff_kwargs(form)

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        results = run_full_model(Path(tmp_path), **tariff_kwargs)
        html = _render_html({}, results)
        return _html_response(html, form.get("project_name"))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def handle_run_report(request: Request) -> Response:
    method_error = ensure_post_method(request)
    if method_error is not None:
        return jsonify({"error": method_error}), 405

    form = dict(request.form)
    source = (form.get("source") or "json").strip().lower()

    try:
        if source == "excel":
            return _handle_excel_source(request, form)
        return _handle_json_source(request, form)
    except REStorageError as exc:
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
    except ValueError as exc:
        if isinstance(exc, json.JSONDecodeError):
            return jsonify(
                {"error": f"Invalid JSON field: {exc}", "type": "JSONDecodeError"}
            ), 400
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
