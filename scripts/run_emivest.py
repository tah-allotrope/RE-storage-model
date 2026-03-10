"""Run Emivest JSON pipeline and generate HTML report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from re_storage.pipeline import run_model_from_json
from re_storage.reporting.html_report import generate_report


def _discover_project_json(project_dir: Path) -> Path:
    json_files = sorted(project_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(
            f"Expected exactly one JSON file in {project_dir}, found {len(json_files)}"
        )
    return json_files[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Emivest model and generate HTML report.")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("tests/data/projects/emivest"),
        help="Project directory containing one .json and one .csv input file.",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Optional reference KPI JSON for comparison table.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/emivest_report.html"),
        help="Output HTML report path.",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    project_json = _discover_project_json(project_dir)
    project_config: dict[str, Any] = json.loads(project_json.read_text(encoding="utf-8"))

    results = run_model_from_json(project_dir)
    lifetime_df = results.pop("_lifetime_df")
    hourly_df = results.pop("_hourly_df")

    reference_data: dict[str, Any] | None = None
    if args.reference is not None:
        reference_data = json.loads(args.reference.resolve().read_text(encoding="utf-8"))

    generate_report(
        project_config=project_config,
        model_results=results,
        reference_kpis=reference_data,
        lifetime_df=lifetime_df,
        hourly_df=hourly_df,
        output_path=args.output.resolve(),
    )

    print(f"Report written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
