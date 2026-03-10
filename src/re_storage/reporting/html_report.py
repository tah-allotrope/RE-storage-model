"""
HTML report generator for JSON-based project runs.
"""

from __future__ import annotations

import base64
import io
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

KPI_TOLERANCES: dict[str, tuple[str, float]] = {
    "project_irr": ("abs", 0.0001),
    "equity_irr": ("abs", 0.0001),
    "unlevered_irr": ("abs", 0.0001),
    "npv_usd": ("rel", 0.0001),
    "dscr_min": ("abs", 0.001),
    "calc_solar_gen_sum_kwh": ("rel", 0.0001),
    "calc_soc_min_kwh": ("rel", 0.0001),
    "calc_soc_max_kwh": ("rel", 0.0001),
    "year1_solar_generation_mwh": ("rel", 0.0001),
    "year1_dppa_revenue_usd": ("rel", 0.0001),
    "year1_grid_savings_usd": ("rel", 0.0001),
}


def _to_base64_png(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        val = float(value)
        if math.isnan(val):
            return None
        return val
    except (TypeError, ValueError):
        return None


def _labelize(key: str) -> str:
    return key.replace("_", " ").title()


def _format_number(value: float, fmt: str = ",.2f") -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "N/A"
    return format(numeric, fmt)


def _comparison_status(
    actual: float,
    expected: float,
    mode: str,
    tolerance: float,
) -> tuple[str, str]:
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is None or e is None:
        return "SKIP", "status-skip"

    if mode == "abs":
        passed = abs(a - e) <= tolerance
    else:
        if abs(e) < 1e-12:
            passed = abs(a - e) <= tolerance
        else:
            passed = abs(a - e) / abs(e) <= tolerance

    if passed:
        return "PASS", "status-pass"
    return "FAIL", "status-fail"


def _render_project_summary(config: dict[str, Any]) -> str:
    system = config.get("system_input", {})
    bess = config.get("bess_parameters", {})
    strategy = config.get("bess_operation_strategy", {})
    timing = config.get("financial_input", {}).get("timing", {})
    cod_serial = timing.get("commercial_operation_date_excel_serial", "N/A")

    return f"""
    <section class=\"card\">
      <h2>Section A - Project Summary</h2>
      <div class=\"grid\">
        <div><strong>Project:</strong> {config.get("project", "N/A")}</div>
        <div><strong>Developer:</strong> {config.get("developer", "N/A")}</div>
        <div><strong>Model:</strong> {config.get("model", "N/A")}</div>
        <div><strong>COD Serial:</strong> {cod_serial}</div>
        <div><strong>PV Capacity (kWp):</strong> {_format_number(system.get("actual_installation_capacity_kWp"), ",.0f")}</div>
        <div><strong>BESS Capacity (kWh):</strong> {_format_number(bess.get("total_bess_storage_capacity_kWh"), ",.0f")}</div>
        <div><strong>BESS Power (kW):</strong> {_format_number(bess.get("total_bess_power_output_kW"), ",.0f")}</div>
        <div><strong>Strategy:</strong> {strategy.get("mode_description", "N/A")}</div>
      </div>
    </section>
    """


def _render_kpi_dashboard(results: dict[str, Any]) -> str:
    return f"""
    <section class=\"card\">
      <h2>Section B - KPI Dashboard</h2>
      <div class=\"kpi-grid\">
        <div class=\"kpi\"><span>Year 1 Solar (MWh)</span><strong>{_format_number(results.get("year1_solar_generation_mwh"), ",.2f")}</strong></div>
        <div class=\"kpi\"><span>Year 1 DPPA Revenue (USD)</span><strong>{_format_number(results.get("year1_dppa_revenue_usd"), ",.2f")}</strong></div>
        <div class=\"kpi\"><span>Year 1 Grid Savings (USD)</span><strong>{_format_number(results.get("year1_grid_savings_usd"), ",.2f")}</strong></div>
        <div class=\"kpi\"><span>Project IRR</span><strong>{_format_number(results.get("project_irr"), ".2%")}</strong></div>
        <div class=\"kpi\"><span>Equity IRR</span><strong>{_format_number(results.get("equity_irr"), ".2%")}</strong></div>
        <div class=\"kpi\"><span>Unlevered IRR</span><strong>{_format_number(results.get("unlevered_irr"), ".2%")}</strong></div>
        <div class=\"kpi\"><span>NPV (USD)</span><strong>{_format_number(results.get("npv_usd"), ",.2f")}</strong></div>
        <div class=\"kpi\"><span>DSCR Min</span><strong>{_format_number(results.get("dscr_min"), ".3f")}</strong></div>
      </div>
    </section>
    """


def _render_comparison_table(results: dict[str, Any], reference: dict[str, Any]) -> str:
    rows: list[str] = []
    for kpi, (mode, tolerance) in KPI_TOLERANCES.items():
        expected = reference.get(kpi)
        actual = results.get(kpi)
        status, css_class = _comparison_status(actual, expected, mode, tolerance)

        a = _safe_float(actual)
        e = _safe_float(expected)
        diff_str = "N/A"
        if a is not None and e is not None:
            if mode == "abs":
                diff_str = _format_number(abs(a - e), ",.6f")
            elif abs(e) < 1e-12:
                diff_str = _format_number(abs(a - e), ",.6f")
            else:
                diff_str = _format_number(abs(a - e) / abs(e), ".4%")

        rows.append(
            "<tr>"
            f"<td>{_labelize(kpi)}</td>"
            f"<td>{_format_number(expected)}</td>"
            f"<td>{_format_number(actual)}</td>"
            f"<td>{diff_str}</td>"
            f"<td>{tolerance if mode == 'abs' else f'{tolerance:.4%}'}</td>"
            f"<td class='{css_class}'>{status}</td>"
            "</tr>"
        )

    return (
        "<section class='card'>"
        "<h2>Section C - Python vs Reference</h2>"
        "<table>"
        "<thead><tr><th>KPI</th><th>Reference</th><th>Python</th><th>Difference</th><th>Tolerance</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</section>"
    )


def _build_annual_figures_df(
    project_config: dict[str, Any],
    lifetime_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
) -> pd.DataFrame:
    tariff_cfg = project_config.get("grid_connection_and_tariff", {}).get(
        "current_applied_evn_tariff_USD_MWh", {}
    )
    off_peak_rate = float(tariff_cfg.get("off_peak", 0.0)) / 1000.0
    standard_rate = float(tariff_cfg.get("standard", 0.0)) / 1000.0
    peak_rate = float(tariff_cfg.get("peak", 0.0)) / 1000.0
    rates = {
        "off_peak": off_peak_rate,
        "standard": standard_rate,
        "peak": peak_rate,
    }

    hourly = hourly_df.copy()
    hourly["time_period_str"] = hourly["time_period"].map(
        lambda x: str(getattr(x, "name", "")).lower()
    )
    hourly["tariff_rate_usd_per_kwh"] = hourly["time_period_str"].map(rates).fillna(standard_rate)

    year1_total_load_mwh = float(hourly["load_kwh"].sum()) / 1000.0
    year1_bess_to_load_mwh = float(hourly["discharged_kw"].sum()) / 1000.0
    year1_pv_saving_revenue_usd = float(
        (hourly["direct_pv_consumption_kw"] * hourly["tariff_rate_usd_per_kwh"]).sum()
    )
    year1_bess_saving_revenue_usd = float(
        (hourly["discharged_kw"] * hourly["tariff_rate_usd_per_kwh"]).sum()
    )

    degradation_rows = project_config.get("degradation_and_loss", {}).get("annual_table", [])
    battery_factor_by_year: dict[int, float] = {}
    for row in degradation_rows:
        if isinstance(row, dict) and "year" in row and "battery_with_replacement" in row:
            battery_factor_by_year[int(row["year"])] = float(row["battery_with_replacement"])

    year1_generation_mwh = float(
        lifetime_df.loc[lifetime_df["year"] == 1, "generation_mwh"].iloc[0]
    )

    annual_rows: list[dict[str, float | int]] = []
    for _, row in lifetime_df.iterrows():
        year = int(row["year"])
        solar_generation_mwh = float(row["generation_mwh"])
        pv_factor = solar_generation_mwh / year1_generation_mwh if year1_generation_mwh > 0 else 0.0
        battery_factor = float(battery_factor_by_year.get(year, 1.0))

        annual_rows.append(
            {
                "year": year,
                "solar_generation_mwh": solar_generation_mwh,
                "bess_to_load_mwh": year1_bess_to_load_mwh * battery_factor,
                "total_load_mwh": year1_total_load_mwh,
                "pv_saving_revenue_usd": year1_pv_saving_revenue_usd * pv_factor,
                "bess_saving_revenue_usd": year1_bess_saving_revenue_usd * battery_factor,
            }
        )

    return pd.DataFrame(annual_rows)


def _render_annual_figures_table(
    project_config: dict[str, Any],
    lifetime_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
) -> str:
    annual_df = _build_annual_figures_df(project_config, lifetime_df, hourly_df)
    rows: list[str] = []
    for _, row in annual_df.iterrows():
        rows.append(
            "<tr>"
            f"<td>{int(row['year'])}</td>"
            f"<td>{_format_number(float(row['solar_generation_mwh']), ',.2f')}</td>"
            f"<td>{_format_number(float(row['bess_to_load_mwh']), ',.2f')}</td>"
            f"<td>{_format_number(float(row['total_load_mwh']), ',.2f')}</td>"
            f"<td>{_format_number(float(row['pv_saving_revenue_usd']), ',.2f')}</td>"
            f"<td>{_format_number(float(row['bess_saving_revenue_usd']), ',.2f')}</td>"
            "</tr>"
        )

    return (
        "<section class='card'>"
        "<h2>Section D - 20-Year Annual Figures</h2>"
        "<table>"
        "<thead><tr>"
        "<th>Year</th>"
        "<th>Solar Generation (MWh)</th>"
        "<th>BESS to Load (MWh)</th>"
        "<th>Total Load (MWh)</th>"
        "<th>PV/Solar Saving Revenue (USD)</th>"
        "<th>BESS Saving Revenue (USD)</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</section>"
    )


def _render_lifetime_charts(lifetime_df: pd.DataFrame) -> str:
    years = lifetime_df["year"]

    fig1, ax1 = plt.subplots(figsize=(10, 3.8))
    ax1.bar(years, lifetime_df["generation_mwh"], color="#24557a")
    ax1.set_title("20-Year Solar Generation")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("MWh")
    img1 = _to_base64_png(fig1)

    fig2, ax2 = plt.subplots(figsize=(10, 3.8))
    ax2.bar(years, lifetime_df["dppa_revenue_usd"], label="DPPA", color="#2c7a7b")
    ax2.bar(
        years,
        lifetime_df["grid_savings_usd"],
        bottom=lifetime_df["dppa_revenue_usd"],
        label="Grid Savings",
        color="#4a90a4",
    )
    ax2.set_title("20-Year Revenue Components")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("USD")
    ax2.legend()
    img2 = _to_base64_png(fig2)

    fig3, ax3 = plt.subplots(figsize=(10, 3.8))
    ax3.plot(years, lifetime_df["battery_capacity_kwh"], color="#b13f3f", linewidth=2)
    ax3.set_title("Battery Capacity Degradation")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("kWh")
    img3 = _to_base64_png(fig3)

    return f"""
    <section class=\"card page-break\">
      <h2>Section E - Lifetime Projection Charts</h2>
      <div class=\"chart-grid\">
        <img alt=\"Solar Generation Chart\" src=\"data:image/png;base64,{img1}\" />
        <img alt=\"Revenue Chart\" src=\"data:image/png;base64,{img2}\" />
        <img alt=\"Battery Degradation Chart\" src=\"data:image/png;base64,{img3}\" />
      </div>
    </section>
    """


def _render_hourly_profile(hourly_df: pd.DataFrame, sample_date: str = "2024-01-15") -> str:
    df = hourly_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    day = pd.Timestamp(sample_date).date()
    sample = df[df["datetime"].dt.date == day]
    if sample.empty:
        sample = df.iloc[:24]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(sample["datetime"], sample["solar_gen_kw"], label="Solar Gen (kW)")
    ax.plot(sample["datetime"], sample["load_kw"], label="Load (kW)")
    ax.plot(sample["datetime"], sample["soc_kwh"], label="SoC (kWh)")
    ax.plot(sample["datetime"], sample["discharged_kw"], label="Discharge (kW)")
    ax.set_title(f"Hourly Profile Sample - {sample.iloc[0]['datetime'].date()}")
    ax.set_xlabel("Time")
    ax.legend(loc="best")
    img = _to_base64_png(fig)

    return f"""
    <section class=\"card page-break\">
      <h2>Section F - Hourly Profile Sample</h2>
      <img alt=\"Hourly Sample Chart\" src=\"data:image/png;base64,{img}\" />
    </section>
    """


def generate_report(
    project_config: dict[str, Any],
    model_results: dict[str, Any],
    reference_kpis: dict[str, Any] | None,
    lifetime_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    output_path: Path | None = None,
) -> str:
    comparison = ""
    if reference_kpis is not None:
        comparison = _render_comparison_table(model_results, reference_kpis)

    html = f"""
    <!doctype html>
    <html lang=\"en\">
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>Emivest Model Report</title>
      <style>
        :root {{
          --ink: #0f1f2e;
          --subtle: #f2f5f8;
          --border: #d3dbe3;
          --pass: #1f7a1f;
          --fail: #b12929;
          --skip: #666;
        }}
        body {{ font-family: Georgia, "Times New Roman", serif; margin: 20px; color: var(--ink); background: #f7f9fb; }}
        h1 {{ margin-bottom: 6px; }}
        h2 {{ margin-top: 0; color: #18354d; }}
        .card {{ background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 8px 18px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 10px; }}
        .kpi {{ background: var(--subtle); border: 1px solid var(--border); border-radius: 6px; padding: 10px; }}
        .kpi span {{ display: block; font-size: 12px; color: #425466; }}
        .kpi strong {{ display: block; font-size: 18px; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        th, td {{ border: 1px solid var(--border); padding: 8px; text-align: left; font-size: 13px; }}
        thead th {{ background: #17324a; color: #fff; }}
        tbody tr:nth-child(even) {{ background: #f8fbfd; }}
        .status-pass {{ color: var(--pass); font-weight: 700; }}
        .status-fail {{ color: var(--fail); font-weight: 700; }}
        .status-skip {{ color: var(--skip); font-weight: 700; }}
        .chart-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; }}
        img {{ width: 100%; border: 1px solid var(--border); background: #fff; }}
        .page-break {{ page-break-before: always; }}
        @media (max-width: 900px) {{
          .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
          .grid {{ grid-template-columns: 1fr; }}
        }}
        @media print {{
          @page {{ size: A4; margin: 15mm; }}
          body {{ margin: 0; background: #fff; }}
          table {{ page-break-inside: avoid; }}
          .card {{ break-inside: avoid; }}
        }}
      </style>
    </head>
    <body>
      <h1>Emivest (Saigon18) - Model Report</h1>
      {_render_project_summary(project_config)}
      {_render_kpi_dashboard(model_results)}
      {comparison}
      {_render_annual_figures_table(project_config, lifetime_df, hourly_df)}
      {_render_lifetime_charts(lifetime_df)}
      {_render_hourly_profile(hourly_df)}
    </body>
    </html>
    """

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    return html
