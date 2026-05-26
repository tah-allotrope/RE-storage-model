#!/usr/bin/env python
"""
Generate a DPPA assessment workbook from a project input.

Orchestrates the full pipeline (physics → settlement → aggregation → financial)
and writes a multi-sheet .xlsx workbook with Cover, Assessment, Comparison,
Sensitivity, and Assumptions sheets.

Usage:
    python scripts/generate_dppa_assessment.py \
        --input tests/data/projects/emivest/ \
        --project-name "Emivest DPPA Assessment" \
        --output reports/dppa_assessment.xlsx

    python scripts/generate_dppa_assessment.py \
        --input "data/project.xlsx" \
        --project-name "Ecoplexus Assessment"
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Ensure the project root is on sys.path so re_storage can be imported.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from re_storage.pipeline import run_full_model, run_model_from_json
from re_storage.reporting.excel_writer import (
    create_workbook,
    save_workbook,
    write_assessment_sheet,
    write_assumptions_sheet,
    write_comparison_sheet,
    write_cover_sheet,
    write_sensitivity_sheet,
)
from re_storage.scenarios.runner import run_all_scenarios
from re_storage.scenarios.sensitivity import run_sensitivity_for_values

logger = logging.getLogger(__name__)

SENSITIVITY_VARIABLES = {
    "strike_price": [0.04, 0.05, 0.055, 0.06, 0.07, 0.08, 0.09],
    "interest_rate": [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10],
    "initial_capex": [15_000_000, 20_000_000, 25_000_000, 30_000_000, 35_000_000],
    "exchange_rate": [23_000, 24_000, 25_000, 26_000, 27_000],
    "bundled_discount": [0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
}


def _detect_input_type(input_path: Path) -> str:
    """Detect whether input is an Excel file or a JSON project directory."""
    if input_path.suffix.lower() == ".xlsx":
        return "excel"
    if input_path.is_dir():
        return "json"
    raise ValueError(f"Cannot detect input type for {input_path}")


def _run_pipeline(input_path: Path, input_type: str, ppa_option: int, topology: str = "onsite") -> dict:
    """Run the pipeline for a single PPA option."""
    if input_type == "excel":
        return run_full_model(input_path, ppa_option=ppa_option, dppa_topology=topology)
    return run_model_from_json(input_path, ppa_option=ppa_option, dppa_topology=topology)


def _extract_exchange_rate(results: dict) -> float:
    """Extract exchange rate from pipeline results for VND conversion."""
    return float(results.get("exchange_rate_usd_vnd", 25_000.0))


def _build_project_metadata(results: dict, input_path: Path) -> dict:
    """Build metadata dict for the cover sheet."""
    return {
        "Input file": input_path.name,
        "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Project IRR": f"{results.get('project_irr', 0):.2%}" if isinstance(results.get("project_irr"), float) else "N/A",
        "Equity IRR": f"{results.get('equity_irr', 0):.2%}" if isinstance(results.get("equity_irr"), float) else "N/A",
        "NPV (USD)": f"{results.get('npv_usd', 0):,.0f}" if isinstance(results.get('npv_usd'), float) else "N/A",
        "Min DSCR": f"{results.get('dscr_min', 0):.2f}" if isinstance(results.get('dscr_min'), float) else "N/A",
    }


def _extract_assumptions(results: dict) -> dict:
    """Extract assumption-like keys from results for the assumptions sheet."""
    skip_keys = {
        "_annual_df", "_hourly_df", "_lifetime_df",
        "project_irr", "equity_irr", "unlevered_irr", "npv_usd",
        "after_tax_project_irr", "after_tax_npv_usd",
        "dscr_min", "dscr_avg", "debt_amount_usd",
        "simple_payback_years", "discounted_payback_year", "cash_on_cash_yield",
        "year1_opex_usd", "year1_ebitda_usd",
        "calc_solar_gen_sum_kwh", "calc_soc_min_kwh", "calc_soc_max_kwh",
        "year1_solar_generation_mwh", "year1_dppa_revenue_usd", "year1_grid_savings_usd",
    }
    return {k: v for k, v in results.items() if k not in skip_keys}


def generate_assessment(
    input_path: Path,
    project_name: str,
    output_path: Path | None = None,
    ppa_options: list[int] | None = None,
    topology: str = "both",
) -> Path:
    """
    Generate a complete DPPA assessment workbook.

    Args:
        input_path: Path to Excel file or JSON project directory.
        project_name: Display name for the workbook.
        output_path: Output .xlsx path. Defaults to reports/dppa_assessment_{date}.xlsx.
        ppa_options: List of PPA option IDs to compare. Defaults to [1, 2, 3, 4].
        topology: "onsite", "offsite", or "both" (default).

    Returns:
        Path to the generated workbook.
    """
    if topology not in {"onsite", "offsite", "both"}:
        raise ValueError(f"topology must be 'onsite', 'offsite', or 'both', got {topology!r}")

    if ppa_options is None:
        ppa_options = [1, 2, 3, 4]

    topologies = ["onsite", "offsite"] if topology == "both" else [topology]

    input_type = _detect_input_type(input_path)
    logger.info("Input type: %s, topology: %s, PPA options: %s", input_type, topology, ppa_options)

    # Default output path
    if output_path is None:
        output_path = _project_root / "reports" / f"dppa_assessment_{datetime.now().strftime('%Y%m%d')}.xlsx"

    # Build workbook
    logger.info("Building workbook...")
    wb = create_workbook()

    # Track results for cover/sensitivity/assumptions (use onsite as default if both)
    first_results = None
    first_annual_df = None
    first_exchange_rate = None

    for topo in topologies:
        logger.info("Running pipeline for topology: %s", topo)

        # Run default pipeline (PPA option 3 = DPPA CfD)
        default_results = _run_pipeline_with_topology(input_path, input_type, ppa_option=3, topology=topo)
        exchange_rate = _extract_exchange_rate(default_results)
        annual_df = default_results.get("_annual_df")

        if first_results is None:
            first_results = default_results
            first_annual_df = annual_df
            first_exchange_rate = exchange_rate

        sheet_name = f"Assessment ({topo.title()})"
        write_assessment_sheet(
            wb,
            sheet_name=sheet_name,
            kpis=default_results,
            annual_df=annual_df,
            exchange_rate_usd_vnd=exchange_rate,
        )

        # Run all scenarios for comparison
        logger.info("Running all scenarios for %s topology...", topo)
        scenario_results = run_all_scenarios(
            project_dir=input_path if input_type == "json" else None,
            excel_path=input_path if input_type == "excel" else None,
            ppa_options=ppa_options,
            dppa_topology=topo,
        )

        comparison_sheet_name = f"Comparison ({topo.title()})"
        write_comparison_sheet(
            wb,
            scenario_results=scenario_results,
            exchange_rate_usd_vnd=exchange_rate,
        )
        # Rename the comparison sheet
        if "Comparison" in wb.sheetnames:
            wb["Comparison"].title = comparison_sheet_name

    # Cover sheet (use first/topology=onsite results)
    cover_results = first_results or {}
    write_cover_sheet(
        wb,
        project_name=project_name,
        project_metadata=_build_project_metadata(cover_results, input_path),
        kpis=cover_results,
    )
    # Move cover to front
    wb.move_sheet("Cover", offset=-len(wb.sheetnames) + 1)

    # Sensitivity (run once with default topology)
    logger.info("Running sensitivity analysis...")
    sensitivity_results: dict[str, dict[float, dict]] = {}
    default_topo = topologies[0]
    for variable_name, test_values in SENSITIVITY_VARIABLES.items():
        try:
            if input_type == "json":
                sensitivity_results[variable_name] = run_sensitivity_for_values(
                    project_dir=input_path,
                    variable_name=variable_name,
                    test_values=test_values,
                    dppa_topology=default_topo,
                )
            else:
                sensitivity_results[variable_name] = run_sensitivity_for_values(
                    excel_path=input_path,
                    variable_name=variable_name,
                    test_values=test_values,
                    dppa_topology=default_topo,
                )
        except Exception as exc:
            logger.warning("Sensitivity for %s failed: %s", variable_name, exc)

    write_sensitivity_sheet(
        wb,
        sensitivity_results=sensitivity_results,
        exchange_rate_usd_vnd=first_exchange_rate or 25_000.0,
    )

    write_assumptions_sheet(
        wb,
        assumptions_dict=_extract_assumptions(cover_results),
    )

    return save_workbook(wb, output_path)


def _run_pipeline_with_topology(
    input_path: Path,
    input_type: str,
    ppa_option: int,
    topology: str,
) -> dict:
    """Run the pipeline with a specific topology."""
    if input_type == "excel":
        return run_full_model(input_path, ppa_option=ppa_option, dppa_topology=topology)
    return run_model_from_json(input_path, ppa_option=ppa_option, dppa_topology=topology)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a DPPA assessment workbook from a project input."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to Excel input file or JSON project directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .xlsx path (default: reports/dppa_assessment_<date>.xlsx).",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        type=str,
        help="Display name for the workbook.",
    )
    parser.add_argument(
        "--ppa-options",
        type=str,
        default="1,2,3,4",
        help="Comma-separated list of PPA option IDs to compare (default: 1,2,3,4).",
    )
    parser.add_argument(
        "--topology",
        type=str,
        default="both",
        choices=["onsite", "offsite", "both"],
        help="Topology mode: 'onsite', 'offsite', or 'both' (default: both).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ppa_options = [int(x.strip()) for x in args.ppa_options.split(",")]

    output_path = generate_assessment(
        input_path=args.input,
        project_name=args.project_name,
        output_path=args.output,
        ppa_options=ppa_options,
        topology=args.topology,
    )

    print(f"\nWorkbook saved to: {output_path}")
    print(f"Sheets: {', '.join(create_workbook().sheetnames)}")


if __name__ == "__main__":
    main()
