"""Serialization helpers for Cloud Function responses."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


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
        for record in lifetime_df.to_dict(orient="records"):
            lifetime.append({k: _sanitize_value(v) for k, v in record.items()})

    return {
        "kpis": kpis,
        "lifetime": lifetime,
    }
