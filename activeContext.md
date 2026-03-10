# Active Context - ISSUE-1 Emivest Test and Report

**Last Updated:** 2026-03-10

## Objective

Implement JSON+CSV support for Emivest (Saigon18), execute the existing simulation pipeline without Excel loaders, compare KPIs against reference JSON, and generate a self-contained HTML report. Additionally, include a 20-year annual figures table with specific metrics.

## Implemented

- Added `matplotlib>=3.7.0` dependency in `pyproject.toml`.
- Created `src/re_storage/inputs/json_loader.py` with:
  - `load_assumptions_from_json()`
  - `load_hourly_data_from_csv()` (handles BOM, drops trailing Unnamed column, normalizes columns)
  - `load_degradation_from_json()`
  - `load_tariff_rates_from_json()`
  - `load_financial_params_from_json()`
  - `_excel_serial_to_date()`
- Updated `src/re_storage/inputs/__init__.py` exports for JSON loader functions.
- Added `run_model_from_json()` to `src/re_storage/pipeline.py`:
  - Discovers exactly one `.json` and one `.csv` in project directory
  - Reuses `_run_physics()`, `_run_settlement()`, `_run_aggregation()`, `_run_financial()`
  - Returns standard KPI dict plus `"_hourly_df"` and `"_lifetime_df"`
  - Uses default tariff schedule (OFF_PEAK 0-6, STANDARD 7-16, PEAK 17-23)
  - Converts hourly FMP/CFMP to USD path using exchange rate from JSON financial params
- Created reporting package:
  - `src/re_storage/reporting/__init__.py`
  - `src/re_storage/reporting/html_report.py` with:
    - `generate_report()`
    - `_render_project_summary()`
    - `_render_kpi_dashboard()`
    - `_render_comparison_table()`
    - `_render_annual_figures_table()` (adds 20-year table of Solar Generation, BESS to Load, Total Load, PV/Solar Saving Revenue, and BESS Saving Revenue)
    - `_render_lifetime_charts()` (inline base64 PNG charts)
    - `_render_hourly_profile()`
    - `_format_number()`
    - `_comparison_status()`
  - Includes inline CSS and print-friendly rules.
- Created CLI script `scripts/run_emivest.py`:
  - `--project-dir` (default `tests/data/projects/emivest`)
  - `--reference` (optional)
  - `--output` (default `reports/emivest_report.html`)
- Created placeholder reference file `tests/data/references/emivest.json` with null KPIs.
- Added unit tests `tests/unit/test_json_loader.py` for loader behavior and edge cases.
- Added regression tests `tests/regression/test_emivest.py` for JSON pipeline execution and KPI checks.

## Verification Status

- `pip install -e ".[dev]"` completed successfully.
- `pytest tests/unit/test_json_loader.py -v` -> **9 passed**.
- `pytest tests/regression/test_emivest.py -v` -> **5 passed, 1 skipped** (reference placeholder).
- `python scripts/run_emivest.py` generated `reports/emivest_report.html` with the new 20-year annual figures table successfully incorporated.
- `pytest -v` -> **189 passed, 1 skipped** (skip is expected: placeholder Emivest reference values).

## Notes / Known Behavior

- Emivest run emits repeated battery strategy overlap warnings from existing battery logic (`when_needed` + `peak`); this behavior is inherited from current dispatch rules and was not changed in this issue.
- The reference comparison test for Emivest intentionally skips until external KPI values are populated in `tests/data/references/emivest.json`.

## Remaining Next Actions

- Fill `tests/data/references/emivest.json` with external reference KPI values.
- Re-run `pytest tests/regression/test_emivest.py -v` to activate full KPI tolerance comparison.
- Optionally refine battery-dispatch warning volume if desired (separate issue).