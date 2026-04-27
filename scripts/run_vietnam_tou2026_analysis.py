from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from re_storage.pipeline import run_full_model, run_model_from_json
from re_storage.scenarios.runner import run_all_scenarios

matplotlib.use("Agg")


ROOT = Path(__file__).resolve().parents[1]
EMIVEST_DIR = ROOT / "tests" / "data" / "projects" / "emivest"
ECOPLEXUS_XLSX = (
    ROOT / "tests" / "data" / "projects" / "AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx"
)
BASELINE_DIR = ROOT / "results" / "baseline"
NEW_TARIFF_DIR = ROOT / "results" / "new_tariff"
FIGURES_DIR = ROOT / "results" / "figures"
ANALYSIS_PATH = ROOT / "results" / "vietnam_tou2026_analysis.json"
REPORT_PATH = ROOT / "results" / "vietnam_tou2026_impact_report.md"
FIGURE_PATH = FIGURES_DIR / "avg_day_dispatch_comparison.png"

PPA_LABELS: dict[int, str] = {
    1: "Bundled Discount",
    2: "Separate PV+BESS",
    3: "DPPA (CfD)",
    4: "Fixed EVN PPA",
}

TARIFF_BANDS_2024: list[tuple[str, int, int, str]] = [
    ("Off-Peak", 0, 4, "#cfe8ff"),
    ("Normal", 4, 9, "#fff0b3"),
    ("Peak", 9, 11, "#f8c4c4"),
    ("Normal", 11, 17, "#fff0b3"),
    ("Peak", 17, 20, "#f8c4c4"),
    ("Normal", 20, 22, "#fff0b3"),
    ("Off-Peak", 22, 24, "#cfe8ff"),
]

TARIFF_BANDS_2026: list[tuple[str, int, int, str]] = [
    ("Off-Peak", 0, 6, "#cfe8ff"),
    ("Normal", 6, 17, "#fff0b3"),
    ("Peak", 17, 22, "#f8c4c4"),
    ("Normal", 22, 24, "#fff0b3"),
]


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _build_single_json_project_dir(parent_dir: Path, json_name: str) -> Path:
    parent_dir.mkdir(parents=True, exist_ok=True)
    source_csv = EMIVEST_DIR / "Emivest additional data.csv"
    source_json = EMIVEST_DIR / json_name
    target_csv = parent_dir / source_csv.name
    target_json = parent_dir / json_name
    target_csv.write_bytes(source_csv.read_bytes())
    target_json.write_bytes(source_json.read_bytes())
    return parent_dir


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def _strip_internal_frames(result: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if not key.startswith("_")}


def _to_serializable_case(result: Mapping[str, Any]) -> dict[str, Any]:
    serializable = dict(_strip_internal_frames(result))

    hourly_df = result.get("_hourly_df")
    if isinstance(hourly_df, pd.DataFrame):
        serializable["average_day_dispatch"] = build_average_day_dispatch(hourly_df).to_dict(
            "records"
        )

    return serializable


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_case_row(
    case_name: str,
    scenario_name: str,
    baseline: Mapping[str, Any],
    new_case: Mapping[str, Any],
) -> dict[str, Any]:
    old_revenue = _to_float(baseline.get("year1_dppa_revenue_usd")) + _to_float(
        baseline.get("year1_grid_savings_usd")
    )
    new_revenue = _to_float(new_case.get("year1_dppa_revenue_usd")) + _to_float(
        new_case.get("year1_grid_savings_usd")
    )
    revenue_delta = new_revenue - old_revenue
    revenue_delta_pct = (revenue_delta / old_revenue * 100.0) if old_revenue else 0.0

    old_project_irr = _to_float(baseline.get("project_irr"))
    new_project_irr = _to_float(new_case.get("project_irr"))

    return {
        "case": case_name,
        "scenario": scenario_name,
        "old_revenue_usd": old_revenue,
        "new_revenue_usd": new_revenue,
        "delta_revenue_usd": revenue_delta,
        "delta_revenue_pct": revenue_delta_pct,
        "old_project_irr": old_project_irr,
        "new_project_irr": new_project_irr,
        "delta_project_irr_pp": (new_project_irr - old_project_irr) * 100.0,
        "old_npv_usd": _to_float(baseline.get("npv_usd")),
        "new_npv_usd": _to_float(new_case.get("npv_usd")),
        "delta_npv_usd": _to_float(new_case.get("npv_usd")) - _to_float(baseline.get("npv_usd")),
        "old_equity_irr": _to_float(baseline.get("equity_irr")),
        "new_equity_irr": _to_float(new_case.get("equity_irr")),
        "old_dscr_min": _to_float(baseline.get("dscr_min")),
        "new_dscr_min": _to_float(new_case.get("dscr_min")),
    }


def _normalize_time_periods(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.lower()
    return normalized.str.split(".").str[-1].str.replace("timeperiod_", "", regex=False)


def build_driver_breakdown(old_hourly: pd.DataFrame, new_hourly: pd.DataFrame) -> dict[str, float]:
    old_period = _normalize_time_periods(old_hourly["time_period"])
    new_period = _normalize_time_periods(new_hourly["time_period"])

    row_count = min(len(old_hourly), len(new_hourly))
    old_aligned = old_hourly.iloc[:row_count].reset_index(drop=True)
    new_aligned = new_hourly.iloc[:row_count].reset_index(drop=True)
    old_period_aligned = old_period.iloc[:row_count].reset_index(drop=True)
    new_period_aligned = new_period.iloc[:row_count].reset_index(drop=True)

    total_delta = float(
        new_hourly["dppa_revenue_usd"].sum()
        + new_hourly["grid_savings_usd"].sum()
        - old_hourly["dppa_revenue_usd"].sum()
        - old_hourly["grid_savings_usd"].sum()
    )

    pv_shift_mask = (
        (old_aligned["direct_pv_consumption_kw"] > 0)
        & (old_period_aligned == "peak")
        & (new_period_aligned != "peak")
    )
    pv_morning_peak_uplift = float(
        new_aligned.loc[pv_shift_mask, "dppa_revenue_usd"].sum()
        - old_aligned.loc[pv_shift_mask, "dppa_revenue_usd"].sum()
    )

    bess_cycle_mask = (
        (old_aligned["discharged_kw"] > new_aligned["discharged_kw"])
        & (old_period_aligned == "peak")
    )
    bess_cycle_reduction = float(
        new_aligned.loc[bess_cycle_mask, "dppa_revenue_usd"].sum()
        - old_aligned.loc[bess_cycle_mask, "dppa_revenue_usd"].sum()
    )

    off_peak_rate_changes = float(
        new_hourly.loc[new_period == "off_peak", "grid_savings_usd"].sum()
        - old_hourly.loc[old_period == "off_peak", "grid_savings_usd"].sum()
    )

    shifted_peak_timing = total_delta - (
        pv_morning_peak_uplift + bess_cycle_reduction + off_peak_rate_changes
    )

    return {
        "Loss of morning peak uplift": pv_morning_peak_uplift,
        "BESS cycle reduction": bess_cycle_reduction,
        "Shifted peak window (timing)": shifted_peak_timing,
        "Off-peak rate changes": off_peak_rate_changes,
    }


def build_average_day_dispatch(hourly_df: pd.DataFrame) -> pd.DataFrame:
    datetimes = pd.to_datetime(hourly_df["datetime"])
    average_day = (
        pd.DataFrame(
            {
                "hour": datetimes.dt.hour,
                "solar_direct_kw": hourly_df["direct_pv_consumption_kw"],
                "bess_discharge_kw": hourly_df["discharged_kw"],
                "grid_import_kw": hourly_df["grid_load_after_re_kw"],
            }
        )
        .groupby("hour", as_index=False)
        .mean(numeric_only=True)
        .sort_values("hour")
        .reset_index(drop=True)
    )
    return average_day


def _format_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def _format_pct(value: float) -> str:
    return f"{value:.2f}%"


def _format_pp(value: float) -> str:
    return f"{value:+.2f} pp"


def _format_ratio(value: float) -> str:
    return f"{value:.2f}x"


def _render_markdown_table(rows: list[dict[str, Any]]) -> str:
    header = (
        "| Case | Scenario | Old Revenue | New Revenue | Delta Revenue | Delta Revenue % | "
        "Old IRR | New IRR | Delta IRR | Delta NPV | Old DSCR | New DSCR |"
    )
    divider = "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, divider]

    for row in rows:
        lines.append(
            (
                "| {case} | {scenario} | {old_revenue} | {new_revenue} | "
                "{delta_revenue} | {delta_revenue_pct} | {old_irr} | {new_irr} | "
                "{delta_irr} | {delta_npv} | {old_dscr} | {new_dscr} |"
            ).format(
                case=row["case"],
                scenario=row["scenario"],
                old_revenue=_format_currency(float(row["old_revenue_usd"])),
                new_revenue=_format_currency(float(row["new_revenue_usd"])),
                delta_revenue=_format_currency(float(row["delta_revenue_usd"])),
                delta_revenue_pct=_format_pct(float(row["delta_revenue_pct"])),
                old_irr=_format_pct(float(row["old_project_irr"]) * 100.0),
                new_irr=_format_pct(float(row["new_project_irr"]) * 100.0),
                delta_irr=_format_pp(float(row["delta_project_irr_pp"])),
                delta_npv=_format_currency(float(row["delta_npv_usd"])),
                old_dscr=_format_ratio(float(row["old_dscr_min"])),
                new_dscr=_format_ratio(float(row["new_dscr_min"])),
            )
        )

    return "\n".join(lines)


def _render_driver_table(rows: list[dict[str, Any]]) -> str:
    header = "| Case | Scenario | Driver | Value |"
    divider = "|---|---|---|---:|"
    lines = [header, divider]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['scenario']} | {row['driver']} | "
            f"{_format_currency(float(row['value_usd']))} |"
        )
    return "\n".join(lines)


def write_average_day_dispatch_chart(
    baseline_dispatch: pd.DataFrame,
    new_dispatch: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    chart_specs = [
        (axes[0], baseline_dispatch, "TOU 2024 Baseline", TARIFF_BANDS_2024),
        (axes[1], new_dispatch, "TOU 2026", TARIFF_BANDS_2026),
    ]

    for ax, dispatch_df, title, bands in chart_specs:
        hours = dispatch_df["hour"]
        solar = dispatch_df["solar_direct_kw"]
        bess = dispatch_df["bess_discharge_kw"]
        grid = dispatch_df["grid_import_kw"]

        for _label, start, end, color in bands:
            ax.axvspan(start, end, color=color, alpha=0.35)

        ax.stackplot(
            hours,
            solar,
            bess,
            grid,
            labels=["Solar direct", "BESS discharge", "Grid import"],
            colors=["#2f7d32", "#bc6c25", "#577590"],
            alpha=0.9,
        )
        ax.set_ylabel("kW")
        ax.set_title(title)
        ax.set_xlim(0, 23)
        ax.set_xticks(range(24))
        ax.grid(axis="y", alpha=0.25)

    axes[1].set_xlabel("Hour of day")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def write_markdown_report(
    report_path: Path,
    summary_lines: list[str],
    comparison_rows: list[dict[str, Any]],
    driver_rows: list[dict[str, Any]],
    figure_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "# Vietnam TOU 2026 Impact Report",
            "",
            "## Executive Summary",
            "",
            *[f"- {line}" for line in summary_lines],
            "",
            "## Tariff Change Description",
            "",
            "| Attribute | Old (<= April 21, 2026) | New (>= April 22, 2026) |",
            "|---|---|---|",
            "| Off-Peak (Mon-Sat) | 22:00-04:00 | 00:00-06:00 |",
            (
                "| Normal (Mon-Sat) | 04:00-09:30, 11:30-17:00, 20:00-22:00 | "
                "06:00-17:30, 22:30-24:00 |"
            ),
            "| Peak (Mon-Sat) | 09:30-11:30 and 17:00-20:00 | 17:30-22:30 |",
            (
                "| Sunday | Normal 04:00-22:00 / Off-Peak 22:00-04:00 | "
                "Normal 06:00-24:00 / Off-Peak 00:00-06:00 |"
            ),
            "| BESS cycles/day | 2 | 1 |",
            "",
            "## Per-Case Results",
            "",
            _render_markdown_table(comparison_rows),
            "",
            "## Revenue Decomposition By Driver",
            "",
            _render_driver_table(driver_rows),
            "",
            "## Average-Day Dispatch Chart",
            "",
            f"![Average day dispatch comparison]({figure_path.as_posix()})",
            "",
            "## Recommended Mitigations",
            "",
            (
                "- Re-price bundled and DPPA offers against the lower evening-only uplift, "
                "especially where solar no longer touches any peak block."
            ),
            (
                "- Re-tune BESS dispatch toward evening peak capture and preserve state "
                "of charge during late-afternoon standard hours."
            ),
            (
                "- Review customer discount assumptions separately for PV-heavy versus "
                "BESS-heavy products because the tariff shift hurts those revenue "
                "stacks differently."
            ),
            (
                "- Keep both tariff baselines in regression artifacts until the 2026 "
                "schedule becomes the production default for every supported project type."
            ),
            "",
        ]
    )
    report_path.write_text(content, encoding="utf-8")


def _read_result_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_full_analysis_payload() -> dict[str, Any]:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    NEW_TARIFF_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_root:
        temp_root_path = Path(temp_root)
        emivest_2024_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2024", "Emivest.json"
        )
        emivest_baseline = run_model_from_json(emivest_2024_dir)
        _write_json(BASELINE_DIR / "emivest_tou2024.json", _strip_internal_frames(emivest_baseline))

        emivest_2026_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2026",
            "Emivest_TOU2026.json",
        )
        emivest_new_tariff = run_all_scenarios(project_dir=emivest_2026_dir)
        for option, result in emivest_new_tariff.items():
            _write_json(
                NEW_TARIFF_DIR / f"emivest_tou2026_option{option}.json",
                _strip_internal_frames(result),
            )

        emivest_tou2026_cycle_cap = run_all_scenarios(
            project_dir=emivest_2026_dir,
            base_params={"max_cycles_per_day": 1},
        )
        for option, result in emivest_tou2026_cycle_cap.items():
            _write_json(
                NEW_TARIFF_DIR / f"emivest_tou2026_option{option}_cyclecap1.json",
                _strip_internal_frames(result),
            )

    ecoplexus_baseline = run_full_model(ECOPLEXUS_XLSX)
    _write_json(BASELINE_DIR / "ecoplexus_tou2024.json", _strip_internal_frames(ecoplexus_baseline))

    ecoplexus_tou2026 = run_full_model(
        ECOPLEXUS_XLSX,
        base_params={"tariff_schedule_sheet": "Tariff Schedule 2026"},
    )
    _write_json(
        NEW_TARIFF_DIR / "ecoplexus_tou2026.json",
        _strip_internal_frames(ecoplexus_tou2026),
    )

    ecoplexus_tou2026_cycle_cap = run_full_model(
        ECOPLEXUS_XLSX,
        base_params={
            "tariff_schedule_sheet": "Tariff Schedule 2026",
            "max_cycles_per_day": 1,
        },
    )
    _write_json(
        NEW_TARIFF_DIR / "ecoplexus_tou2026_cyclecap1.json",
        _strip_internal_frames(ecoplexus_tou2026_cycle_cap),
    )

    return {
        "baseline": {
            "emivest": _to_serializable_case(emivest_baseline),
            "ecoplexus": _to_serializable_case(ecoplexus_baseline),
        },
        "new_tariff": {
            "emivest": {
                f"option_{option}": _to_serializable_case(result)
                for option, result in emivest_new_tariff.items()
            },
            "emivest_cyclecap1": {
                f"option_{option}": _to_serializable_case(result)
                for option, result in emivest_tou2026_cycle_cap.items()
            },
            "ecoplexus": _to_serializable_case(ecoplexus_tou2026),
            "ecoplexus_cyclecap1": _to_serializable_case(ecoplexus_tou2026_cycle_cap),
        },
    }


def _ensure_analysis_payload() -> dict[str, Any]:
    if ANALYSIS_PATH.exists():
        return _read_result_json(ANALYSIS_PATH)

    analysis = _build_full_analysis_payload()
    _write_json(ANALYSIS_PATH, analysis)
    return analysis


def _load_hourly_from_model_runs() -> dict[str, pd.DataFrame]:
    with tempfile.TemporaryDirectory() as temp_root:
        temp_root_path = Path(temp_root)
        emivest_2024_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2024", "Emivest.json"
        )
        emivest_baseline = run_model_from_json(emivest_2024_dir)

        emivest_2026_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2026",
            "Emivest_TOU2026.json",
        )
        emivest_option1 = run_model_from_json(emivest_2026_dir, ppa_option=1)

    hourly_frames = {
        "emivest_baseline": emivest_baseline["_hourly_df"].copy(),
        "emivest_new": emivest_option1["_hourly_df"].copy(),
    }
    return hourly_frames


def _build_summary_lines(comparison_rows: list[dict[str, Any]]) -> list[str]:
    worst_revenue = min(comparison_rows, key=lambda row: float(row["delta_revenue_pct"]))
    best_revenue = max(comparison_rows, key=lambda row: float(row["delta_revenue_pct"]))
    largest_npv = max(comparison_rows, key=lambda row: abs(float(row["delta_npv_usd"])))
    ecoplexus_row = next(row for row in comparison_rows if row["case"] == "Ecoplexus 40MW")

    return [
        (
            f"Worst revenue hit: {worst_revenue['case']} {worst_revenue['scenario']} moved by "
            f"{_format_currency(float(worst_revenue['delta_revenue_usd']))} "
            f"({_format_pct(float(worst_revenue['delta_revenue_pct']))})."
        ),
        (
            f"Best preserved case: {best_revenue['case']} {best_revenue['scenario']} moved by "
            f"{_format_currency(float(best_revenue['delta_revenue_usd']))} "
            f"({_format_pct(float(best_revenue['delta_revenue_pct']))})."
        ),
        (
            f"Largest NPV movement: {largest_npv['case']} {largest_npv['scenario']} shifted by "
            f"{_format_currency(float(largest_npv['delta_npv_usd']))}."
        ),
        (
            f"Ecoplexus project IRR changed from "
            f"{_format_pct(float(ecoplexus_row['old_project_irr']) * 100.0)} "
            f"to {_format_pct(float(ecoplexus_row['new_project_irr']) * 100.0)}."
        ),
    ]


def generate_phase5_and_phase6_outputs() -> dict[str, Any]:
    analysis_payload = _build_full_analysis_payload()
    _write_json(ANALYSIS_PATH, analysis_payload)

    baseline_emivest = analysis_payload["baseline"]["emivest"]
    baseline_ecoplexus = analysis_payload["baseline"]["ecoplexus"]

    comparison_rows: list[dict[str, Any]] = []
    for option in sorted(PPA_LABELS):
        new_case = analysis_payload["new_tariff"]["emivest"][f"option_{option}"]
        comparison_rows.append(
            build_case_row(
                case_name="Emivest",
                scenario_name=PPA_LABELS[option],
                baseline=baseline_emivest,
                new_case=new_case,
            )
        )

    comparison_rows.append(
        build_case_row(
            case_name="Ecoplexus 40MW",
            scenario_name="DPPA (CfD)",
            baseline=baseline_ecoplexus,
            new_case=analysis_payload["new_tariff"]["ecoplexus"],
        )
    )

    hourly_frames = _load_hourly_from_model_runs()

    driver_rows: list[dict[str, Any]] = []
    for driver, value in build_driver_breakdown(
        hourly_frames["emivest_baseline"], hourly_frames["emivest_new"]
    ).items():
        driver_rows.append(
            {
                "case": "Emivest",
                "scenario": "Bundled Discount",
                "driver": driver,
                "value_usd": value,
            }
        )

    baseline_dispatch = build_average_day_dispatch(hourly_frames["emivest_baseline"])
    new_dispatch = build_average_day_dispatch(hourly_frames["emivest_new"])
    write_average_day_dispatch_chart(baseline_dispatch, new_dispatch, FIGURE_PATH)

    summary_lines = _build_summary_lines(comparison_rows)
    write_markdown_report(
        REPORT_PATH,
        summary_lines=summary_lines,
        comparison_rows=comparison_rows,
        driver_rows=driver_rows,
        figure_path=FIGURE_PATH.relative_to(REPORT_PATH.parent),
    )

    analysis_payload["phase5"] = {
        "comparison_rows": comparison_rows,
        "driver_rows": driver_rows,
        "figure_path": str(FIGURE_PATH.relative_to(ROOT)),
    }
    analysis_payload["phase6"] = {
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "summary_lines": summary_lines,
    }
    _write_json(ANALYSIS_PATH, analysis_payload)
    return analysis_payload


def main() -> None:
    generate_phase5_and_phase6_outputs()


if __name__ == "__main__":
    main()
