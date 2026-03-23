"""Serialization helpers for Cloud Function responses."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

ANNUAL_COLUMNS = [
    "year",
    "dppa_revenue_usd",
    "grid_savings_usd",
    "demand_charge_savings_usd",
    "total_revenue_usd",
    "total_opex_usd",
    "ebitda_usd",
    "total_debt_service_usd",
    "cfads_usd",
    "taxes_usd",
    "mra_contribution_usd",
    "free_cash_flow_to_equity_usd",
    "capex_usd",
    "dscr",
]
CASHFLOW_COLUMNS = [
    "year",
    "ebitda_usd",
    "cfads_usd",
    "free_cash_flow_to_equity_usd",
    "capex_usd",
]
DSCR_COLUMNS = ["year", "dscr", "total_debt_service_usd", "cfads_usd"]
DISPATCH_COLUMNS = [
    "datetime",
    "soc_kwh",
    "solar_gen_kw",
    "load_kw",
    "direct_pv_consumption_kw",
    "pv_charged_kw",
    "grid_charged_kw",
    "discharged_kw",
    "grid_load_after_re_kw",
]
DISPATCH_SAMPLE_HOURS = 24 * 7


def _sanitize_value(value: Any) -> Any:
    if value is pd.NA:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and callable(value.item):
        try:
            return _sanitize_value(value.item())
        except (ValueError, TypeError):
            return value
    return value


def _serialise_dataframe_rows(dataframe: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    available_columns = [column for column in columns if column in dataframe.columns]
    if not available_columns:
        return []

    rows: list[dict[str, Any]] = []
    for record in dataframe.loc[:, available_columns].to_dict(orient="records"):
        rows.append({key: _sanitize_value(value) for key, value in record.items()})
    return rows


def serialise_results(results: dict[str, Any]) -> dict[str, Any]:
    """Convert model output to JSON-safe payload for API clients."""
    kpis: dict[str, Any] = {}
    for key, value in results.items():
        if key.startswith("_"):
            continue
        kpis[key] = _sanitize_value(value)

    lifetime_df = results.get("_lifetime_df")
    lifetime: list[dict[str, Any]] = []
    if isinstance(lifetime_df, pd.DataFrame):
        lifetime = _serialise_dataframe_rows(lifetime_df, list(lifetime_df.columns))

    annual_df = results.get("_annual_df")
    annual: list[dict[str, Any]] = []
    cashflow: list[dict[str, Any]] = []
    dscr_series: list[dict[str, Any]] = []
    if isinstance(annual_df, pd.DataFrame):
        annual = _serialise_dataframe_rows(annual_df, ANNUAL_COLUMNS)
        cashflow = _serialise_dataframe_rows(annual_df, CASHFLOW_COLUMNS)
        dscr_series = _serialise_dataframe_rows(annual_df, DSCR_COLUMNS)

    hourly_df = results.get("_hourly_df")
    dispatch_sample: list[dict[str, Any]] = []
    if isinstance(hourly_df, pd.DataFrame):
        dispatch_sample = _serialise_dataframe_rows(
            hourly_df.head(DISPATCH_SAMPLE_HOURS),
            DISPATCH_COLUMNS,
        )

    return {
        "kpis": kpis,
        "lifetime": lifetime,
        "annual": annual,
        "cashflow": cashflow,
        "dscr_series": dscr_series,
        "dispatch_sample": dispatch_sample,
    }
