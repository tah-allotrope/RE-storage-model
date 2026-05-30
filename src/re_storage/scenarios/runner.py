"""
Scenario comparison runner.

Runs the full pipeline for each of the 4 PPA options and returns a
side-by-side comparison dict, mirroring the Excel Scenarios sheet.

Excel source: Scenarios!B–E columns (Year-1 revenue, EBITDA, 20-year totals)
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# PPA option labels for display
PPA_OPTION_LABELS: dict[int, str] = {
    1: "Bundled Discount",
    2: "Separate PV+BESS",
    3: "DPPA (CfD)",
    4: "Fixed EVN PPA",
}


def run_all_scenarios(
    project_dir: Path | None = None,
    excel_path: Path | None = None,
    base_params: dict[str, Any] | None = None,
    ppa_options: list[int] | None = None,
    dppa_topology: str = "onsite",
    tariff_mode: str = "1-component",
) -> dict[int, dict[str, Any]]:
    """
    Run the full pipeline for each PPA option and return a comparison dict.

    One of project_dir (JSON+CSV) or excel_path must be provided.
    If base_params is provided, it overrides loader outputs.

    Excel source: Scenarios!A1–N73 — side-by-side KPI comparison per option.

    Args:
        project_dir: Path to directory with one JSON + one CSV file.
        excel_path: Path to Excel input file.
        base_params: Optional override dict for financial/scenario params.
        ppa_options: List of PPA option integers to run (default: [1, 2, 3, 4]).

    Returns:
        Dict mapping {ppa_option: kpi_dict} for each requested scenario.
        Each kpi_dict is the same structure returned by run_full_model /
        run_model_from_json, plus 'ppa_option' and 'ppa_label' keys.

    Raises:
        ValueError: If neither project_dir nor excel_path is provided.
    """
    from re_storage.pipeline import run_full_model, run_model_from_json

    if dppa_topology not in {"onsite", "offsite"}:
        raise ValueError(f"dppa_topology must be 'onsite' or 'offsite', got {dppa_topology!r}")

    if project_dir is None and excel_path is None:
        raise ValueError("Either project_dir or excel_path must be provided.")

    if ppa_options is None:
        ppa_options = [1, 2, 3, 4]

    results: dict[int, dict[str, Any]] = {}
    for option in ppa_options:
        logger.info("Running scenario: PPA option %d (%s)", option, PPA_OPTION_LABELS.get(option))
        try:
            if excel_path is not None:
                kpis = run_full_model(
                    Path(excel_path),
                    ppa_option=option,
                    base_params=base_params,
                    dppa_topology=dppa_topology,
                    tariff_mode=tariff_mode,
                )
            else:
                kpis = run_model_from_json(
                    Path(project_dir),
                    ppa_option=option,
                    base_params=base_params,
                    dppa_topology=dppa_topology,
                    tariff_mode=tariff_mode,
                )
            kpis = dict(kpis)
            kpis["ppa_option"] = option
            kpis["ppa_label"] = PPA_OPTION_LABELS.get(option, f"Option {option}")
            results[option] = kpis
        except Exception as exc:
            logger.warning("PPA option %d failed: %s", option, exc)
            results[option] = {
                "ppa_option": option,
                "ppa_label": PPA_OPTION_LABELS.get(option, f"Option {option}"),
                "error": str(exc),
            }

    return results
