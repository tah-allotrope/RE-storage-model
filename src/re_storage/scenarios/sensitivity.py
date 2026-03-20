"""
Sensitivity analysis engine.

Sweeps a single parameter across a range of test values, runs the full
pipeline for each, and returns the resulting KPI dict per value.

Excel source: Scenarios!A17–N35 (9-variable × 7-value sensitivity matrix)
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Supported sensitivity variables and the financial_params key they map to.
# The pipeline accepts these as overrides in base_params.
SENSITIVITY_VARIABLES: dict[str, str] = {
    "strike_price_vnd": "strike_price_vnd",
    "interest_rate_pct": "interest_rate_pct",
    "pv_capex_usd_per_mwp": "pv_capex_usd_per_mwp",
    "bess_capex_usd_per_mwh": "bess_capex_usd_per_mwh",
    "fx_rate": "exchange_rate_usd_vnd",
    "max_leverage": "max_leverage_ratio",
    "opex_escalation_pct": "opex_escalation_pct",
    "revenue_escalation_pct": "revenue_escalation_pct",
    "bundled_discount_pct": "bundled_discount_pct",
}


def run_sensitivity(
    variable_name: str,
    test_values: list[float],
    project_dir: Path | None = None,
    excel_path: Path | None = None,
    base_params: dict[str, Any] | None = None,
    ppa_option: int = 3,
) -> dict[float, dict[str, Any]]:
    """
    Run the full pipeline for each value of a single sensitivity variable.

    One of project_dir (JSON+CSV) or excel_path must be provided.

    Excel source: Scenarios!A17–N35

    Args:
        variable_name: Name of variable to sweep. Must be one of
            SENSITIVITY_VARIABLES keys or a direct financial_params key.
        test_values: List of values to test for the variable.
        project_dir: Path to directory with one JSON + one CSV file.
        excel_path: Path to Excel input file.
        base_params: Optional base parameter overrides (applied before sweep).
        ppa_option: PPA option to use for all runs (default 3 = DPPA).

    Returns:
        Dict mapping {test_value: kpi_dict} for each test value.

    Raises:
        ValueError: If neither project_dir nor excel_path is provided.
    """
    from re_storage.pipeline import run_full_model, run_model_from_json

    if project_dir is None and excel_path is None:
        raise ValueError("Either project_dir or excel_path must be provided.")

    # Resolve variable key
    param_key = SENSITIVITY_VARIABLES.get(variable_name, variable_name)

    results: dict[float, dict[str, Any]] = {}
    for value in test_values:
        logger.info("Sensitivity: %s = %s", variable_name, value)
        params = copy.deepcopy(base_params or {})
        params[param_key] = value

        try:
            if excel_path is not None:
                kpis = run_full_model(Path(excel_path), ppa_option=ppa_option, **params)
            else:
                kpis = run_model_from_json(Path(project_dir), ppa_option=ppa_option)
            kpis = dict(kpis)
            kpis["sensitivity_variable"] = variable_name
            kpis["sensitivity_value"] = value
            results[value] = kpis
        except Exception as exc:
            logger.warning("Sensitivity %s=%s failed: %s", variable_name, value, exc)
            results[value] = {
                "sensitivity_variable": variable_name,
                "sensitivity_value": value,
                "error": str(exc),
            }

    return results
