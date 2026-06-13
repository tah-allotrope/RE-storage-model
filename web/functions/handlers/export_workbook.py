"""Handler for Excel workbook downloads (single-run scope).

Re-runs the model from posted inputs and builds a branded ``.xlsx`` workbook
with Cover, Assumptions, and Assessment sheets - the single-run MVP scope
agreed in the GAP-02 plan (Q-001). Multi-scenario and sensitivity sheets
require :func:`re_storage.scenarios.runner.run_all_scenarios` and may blow
through the Cloud Function timeout; they are intentionally out of scope and
will be gated behind a ``?full=true`` flag in a follow-up.

Supports the same two input sources as ``run_report`` via the ``source`` form
field: ``json`` (default) or ``excel``.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Request, Response, jsonify
from utils.validate import ensure_post_method, ensure_uploaded_file

from handlers.project_payload import build_project_payload, resolve_tariff_mode, to_float
from re_storage.core.exceptions import REStorageError
from re_storage.pipeline import run_full_model, run_model_from_json
from re_storage.reporting.assessment import assess_project
from re_storage.reporting.excel_writer import (
    create_workbook,
    save_workbook,
    write_assessment_sheet,
    write_assumptions_sheet,
    write_cover_sheet,
)

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_XLSX_HEADERS = {
    "Content-Type": _XLSX_MIME,
    "Access-Control-Expose-Headers": "Content-Disposition",
}

# Keys that are KPI outputs (excluded from the assumptions sheet) - mirrors
# scripts/generate_dppa_assessment.py::_extract_assumptions to keep the
# workbook's Assumptions sheet meaningful rather than echoing the KPI grid.
_ASSUMPTION_SKIP_KEYS = {
    "_annual_df",
    "_hourly_df",
    "_lifetime_df",
    "project_irr",
    "equity_irr",
    "unlevered_irr",
    "npv_usd",
    "after_tax_project_irr",
    "after_tax_npv_usd",
    "dscr_min",
    "dscr_avg",
    "debt_amount_usd",
    "simple_payback_years",
    "discounted_payback_year",
    "cash_on_cash_yield",
    "year1_opex_usd",
    "year1_ebitda_usd",
    "calc_solar_gen_sum_kwh",
    "calc_soc_min_kwh",
    "calc_soc_max_kwh",
    "year1_solar_generation_mwh",
    "year1_dppa_revenue_usd",
    "year1_grid_savings_usd",
}


def _slugify(value: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in value.lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "project"


def _filename(project_name: str | None) -> str:
    base = _slugify((project_name or "").strip())
    stamp = datetime.now().strftime("%Y%m%d")
    return f"re-storage-workbook-{base}-{stamp}.xlsx"


def _project_metadata(results: dict[str, Any], source: str) -> dict[str, Any]:
    def _pct(key: str) -> str:
        value = results.get(key)
        return f"{value:.2%}" if isinstance(value, float) else "N/A"

    def _money(key: str) -> str:
        value = results.get(key)
        return f"{value:,.0f}" if isinstance(value, float) else "N/A"

    def _ratio(key: str) -> str:
        value = results.get(key)
        return f"{value:.2f}" if isinstance(value, float) else "N/A"

    return {
        "Source": source,
        "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Project IRR": _pct("project_irr"),
        "Equity IRR": _pct("equity_irr"),
        "NPV (USD)": _money("npv_usd"),
        "Min DSCR": _ratio("dscr_min"),
    }


def _assumptions(results: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in results.items() if key not in _ASSUMPTION_SKIP_KEYS}


def _build_workbook_bytes(
    results: dict[str, Any], project_name: str, source_label: str
) -> bytes:
    annual_df = results.get("_annual_df")
    if annual_df is None or (isinstance(annual_df, pd.DataFrame) and annual_df.empty):
        raise REStorageError(
            "Model run did not produce an annual proforma required for the workbook"
        )

    exchange_rate = float(results.get("exchange_rate_usd_vnd", 25_000.0) or 25_000.0)
    kpis_for_sheets = {key: value for key, value in results.items() if not key.startswith("_")}
    verdict = assess_project(kpis_for_sheets)

    wb = create_workbook()
    write_cover_sheet(
        wb,
        project_name=project_name,
        project_metadata=_project_metadata(results, source_label),
        kpis=kpis_for_sheets,
        verdict=verdict,
    )
    write_assumptions_sheet(wb, assumptions_dict=_assumptions(kpis_for_sheets))
    write_assessment_sheet(
        wb,
        sheet_name="Assessment",
        kpis=kpis_for_sheets,
        annual_df=annual_df,
        exchange_rate_usd_vnd=exchange_rate,
        charts=None,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "workbook.xlsx"
        save_workbook(wb, out_path)
        return out_path.read_bytes()


def _xlsx_response(body: bytes, project_name: str | None) -> Response:
    headers = dict(_XLSX_HEADERS)
    headers["Content-Disposition"] = f'attachment; filename="{_filename(project_name)}"'
    return Response(body, status=200, headers=headers)


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
        body = _build_workbook_bytes(
            results,
            project_name=form.get("project_name") or "RE-Storage Project",
            source_label="JSON form",
        )
        return _xlsx_response(body, form.get("project_name"))


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
        body = _build_workbook_bytes(
            results,
            project_name=form.get("project_name") or "RE-Storage Project",
            source_label=f"Excel upload ({filename})",
        )
        return _xlsx_response(body, form.get("project_name"))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def handle_export_workbook(request: Request) -> Response:
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
