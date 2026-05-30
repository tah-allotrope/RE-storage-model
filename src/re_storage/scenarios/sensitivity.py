"""
Sensitivity analysis engine.

Sweeps a single parameter across a symmetric 7-point range and runs the
full pipeline for each scenario, then aggregates results into DataFrames
suitable for tornado chart generation.

Excel source: Scenarios!A17–N35 (9-variable × 7-value sensitivity matrix)

Public API
----------
``run_sensitivity(base_params, variable_name, steps=7)``
    Sweep one variable; return list of (param_value, irr, npv, dscr_min).

``run_full_sensitivity(base_params)``
    Sweep all 9 standard variables; return dict keyed by variable name.

``build_sensitivity_dataframe(full_results)``
    Convert ``run_full_sensitivity`` output into a pandas DataFrame that
    is ready for tornado chart generation.

``plot_tornado_chart(df, output_path, metric="irr_range")``
    Render a horizontal bar tornado chart and save to *output_path*.

Lower-level helper
------------------
``run_sensitivity_for_values(variable_name, test_values, ...)``
    Original programmatic API: accepts an explicit list of test values.
    Retained for backward compatibility and advanced use cases.
"""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Variable definitions
# ---------------------------------------------------------------------------

# For each sensitivity variable we record:
#   param_key   — key in the financial_params / base_params dict
#   step_type   — "relative" (fraction of base) or "absolute" (additive)
#   step_size   — magnitude of one step
#                 • relative: fraction, e.g. 1/15 ≈ 0.0667 means ±6.67 % per step
#                 • absolute: raw value, e.g. 0.00667 for ~67 bps
#
# The 7 test points are:
#   base × (1 + k × step_size)  for k in {-3, -2, -1, 0, +1, +2, +3}  (relative)
#   base +  k × step_size        for k in {-3, -2, -1, 0, +1, +2, +3}  (absolute)
#
# Step sizes are chosen so that ±3 steps covers the intended ±range:
#   ±20 %  → step = 20/3 % ≈ 6.67 % per step
#   ±30 %  → step = 10 % per step
#   ±200 bps (interest) → step = 200/3 bps ≈ 0.667 % per step (absolute)
#   ±5 %  (discount)   → step = 5/3 % ≈ 0.0167 absolute
#   ±2 %  (escalation) → step = 2/3 % ≈ 0.00667 absolute


class _VarConfig(NamedTuple):
    """Internal configuration for one sensitivity variable."""

    param_key: str
    """Key in base_params dict that maps to this variable."""
    step_type: str
    """Either 'relative' or 'absolute'."""
    step_size: float
    """Magnitude of one step (see module docstring)."""
    display_name: str
    """Human-readable label for chart axes."""
    default_base: float
    """Fallback base value if not present in base_params."""


#: Standard 9-variable sensitivity matrix from ``Scenarios!A17–N35``.
SENSITIVITY_VARIABLES: dict[str, _VarConfig] = {
    # 1. PPA strike price ±20 %
    "strike_price_vnd": _VarConfig(
        param_key="strike_price_vnd",
        step_type="relative",
        step_size=20.0 / 3.0 / 100.0,  # ≈ 6.67 % per step
        display_name="PPA Strike Price (VND/kWh)",
        default_base=1800.0,
    ),
    # 2. Solar CAPEX ±20 %
    "pv_capex_usd_per_mwp": _VarConfig(
        param_key="pv_capex_usd_per_mwp",
        step_type="relative",
        step_size=20.0 / 3.0 / 100.0,
        display_name="Solar CAPEX (USD/MWp)",
        default_base=750_000.0,
    ),
    # 3. BESS CAPEX ±20 %
    "bess_capex_usd_per_mwh": _VarConfig(
        param_key="bess_capex_usd_per_mwh",
        step_type="relative",
        step_size=20.0 / 3.0 / 100.0,
        display_name="BESS CAPEX (USD/MWh)",
        default_base=200_000.0,
    ),
    # 4. BESS size ±30 %
    "bess_size_mwh": _VarConfig(
        param_key="bess_mwh",
        step_type="relative",
        step_size=10.0 / 100.0,  # 10 % per step → ±30 %
        display_name="BESS Size (MWh)",
        default_base=66.0,
    ),
    # 5. Solar capacity ±20 %
    "solar_capacity_mwp": _VarConfig(
        param_key="installed_pv_mwp",
        step_type="relative",
        step_size=20.0 / 3.0 / 100.0,
        display_name="Solar Capacity (MWp)",
        default_base=40.36,
    ),
    # 6. Debt interest rate ±200 bps (absolute change in %)
    "interest_rate_pct": _VarConfig(
        param_key="interest_rate_pct",
        step_type="absolute",
        step_size=2.0 / 3.0 / 100.0,  # ≈ 0.00667 (i.e. ~67 bps as fraction)
        display_name="Debt Interest Rate (%)",
        default_base=0.065,
    ),
    # 7. DPPA discount to EVN ±5 % (absolute)
    "bundled_discount_pct": _VarConfig(
        param_key="bundled_discount_pct",
        step_type="absolute",
        step_size=5.0 / 3.0 / 100.0,  # ≈ 0.01667 absolute per step
        display_name="DPPA Discount to EVN (%)",
        default_base=0.15,
    ),
    # 8. CPI / OPEX escalation ±2 % (absolute)
    "opex_escalation_pct": _VarConfig(
        param_key="opex_escalation_pct",
        step_type="absolute",
        step_size=2.0 / 3.0 / 100.0,  # ≈ 0.00667 absolute per step
        display_name="OPEX Escalation Rate (%)",
        default_base=0.04,
    ),
    # 9. FMP price trajectory ±20 % (absolute change on the descent rate)
    "fmp_descent_pct": _VarConfig(
        param_key="fmp_descent_pct",
        step_type="absolute",
        step_size=20.0 / 3.0 / 100.0,  # ≈ 0.00667 absolute per step
        display_name="FMP Price Trajectory (%/yr)",
        default_base=-0.05,
    ),
}

# Publicly accessible list of standard variable names
STANDARD_VARIABLE_NAMES: list[str] = list(SENSITIVITY_VARIABLES.keys())


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


class SensitivityPoint(NamedTuple):
    """
    Result for one parameter value in a sensitivity sweep.

    Attributes
    ----------
    param_value:
        The test value of the swept parameter.
    irr:
        Project IRR (pre-tax unlevered) at this parameter value.
    npv:
        Project NPV (USD) at this parameter value.
    dscr_min:
        Minimum DSCR across the debt tenor at this parameter value.
    equity_irr:
        Equity IRR at this parameter value.
    """

    param_value: float
    irr: float
    npv: float
    dscr_min: float
    equity_irr: float


# ---------------------------------------------------------------------------
# Core sweep functions
# ---------------------------------------------------------------------------


def _compute_test_values(
    var_name: str,
    base_params: dict[str, Any],
    steps: int,
) -> list[float]:
    """
    Build the symmetric test-value list for *var_name* centred on its base.

    Args:
        var_name: Key in ``SENSITIVITY_VARIABLES``.
        base_params: Must contain the param_key for *var_name*, or the
            ``_VarConfig.default_base`` is used.
        steps: Total number of test values.  Must be odd (e.g. 7).

    Returns:
        List of ``steps`` test values, sorted ascending.

    Raises:
        ValueError: If ``steps`` is even or ``var_name`` is unknown.
    """
    if steps % 2 == 0:
        raise ValueError(f"steps must be odd (got {steps}). Use 7 for ±3-step sweep.")

    if var_name not in SENSITIVITY_VARIABLES:
        raise ValueError(
            f"Unknown sensitivity variable {var_name!r}. "
            f"Known variables: {sorted(SENSITIVITY_VARIABLES)}"
        )

    cfg = SENSITIVITY_VARIABLES[var_name]
    base = float(base_params.get(cfg.param_key, cfg.default_base))
    half = steps // 2  # number of steps on each side (e.g. 3 for steps=7)

    values: list[float] = []
    for k in range(-half, half + 1):
        if cfg.step_type == "relative":
            values.append(base * (1.0 + k * cfg.step_size))
        else:  # absolute
            values.append(base + k * cfg.step_size)

    return values


def run_sensitivity(
    base_params: dict[str, Any],
    variable_name: str,
    steps: int = 7,
) -> list[SensitivityPoint]:
    """
    Sweep one sensitivity variable across a symmetric ``steps``-point range.

    The base value is read from ``base_params`` (falling back to the
    variable's ``default_base`` if not present).  All other parameters are
    held at their ``base_params`` values.

    The pipeline is run via ``run_full_model`` (Excel path) or
    ``run_model_from_json`` (JSON+CSV directory), determined by the presence
    of ``"excel_path"`` or ``"project_dir"`` in ``base_params``.

    Args:
        base_params: Dict of model parameters.  **Must** contain either
            ``"excel_path"`` (``str | Path``) pointing to an Excel input
            file, *or* ``"project_dir"`` (``str | Path``) pointing to a
            directory with one JSON and one CSV file.  All other keys are
            forwarded to the pipeline as parameter overrides.
        variable_name: Name of the variable to sweep.  Must be one of
            ``STANDARD_VARIABLE_NAMES`` or any key accepted directly by
            the pipeline financial-params dict.
        steps: Number of test points.  Must be odd.  Default is 7,
            producing the Excel-equivalent {base–3Δ, …, base, …, base+3Δ}
            sweep.

    Returns:
        List of ``SensitivityPoint`` named-tuples, one per test value,
        sorted by ``param_value`` ascending.  If a run fails, the KPI
        fields are ``float("nan")``.

    Raises:
        ValueError: If neither ``excel_path`` nor ``project_dir`` is in
            ``base_params``, or if ``variable_name`` is invalid, or if
            ``steps`` is even.

    Example::

        results = run_sensitivity(
            base_params={"excel_path": "project.xlsx"},
            variable_name="pv_capex_usd_per_mwp",
        )
        for pt in results:
            print(f"CAPEX={pt.param_value:.0f}  IRR={pt.irr:.2%}")
    """
    from re_storage.pipeline import run_full_model, run_model_from_json

    excel_path = base_params.get("excel_path")
    project_dir = base_params.get("project_dir")

    if excel_path is None and project_dir is None:
        raise ValueError("base_params must contain either 'excel_path' or 'project_dir'.")

    # Resolve to param_key (allowing custom keys not in SENSITIVITY_VARIABLES)
    if variable_name in SENSITIVITY_VARIABLES:
        param_key = SENSITIVITY_VARIABLES[variable_name].param_key
    else:
        param_key = variable_name

    test_values = _compute_test_values(variable_name, base_params, steps)

    ppa_option: int = int(base_params.get("ppa_option", 3))
    points: list[SensitivityPoint] = []

    for value in test_values:
        logger.info("Sensitivity: %s = %.6g", variable_name, value)
        params_override = {
            k: v for k, v in base_params.items() if k not in {"excel_path", "project_dir"}
        }
        params_override[param_key] = value

        try:
            if excel_path is not None:
                kpis = run_full_model(
                    Path(excel_path),
                    ppa_option=ppa_option,
                    base_params={
                        k: v for k, v in params_override.items() if k not in {"ppa_option"}
                    },
                )
            else:
                kpis = run_model_from_json(
                    Path(project_dir),
                    ppa_option=ppa_option,
                    base_params=params_override,
                )
                kpis = dict(kpis)

            point = SensitivityPoint(
                param_value=float(value),
                irr=float(kpis.get("project_irr", float("nan"))),
                npv=float(kpis.get("npv_usd", float("nan"))),
                dscr_min=float(kpis.get("dscr_min", float("nan"))),
                equity_irr=float(kpis.get("equity_irr", float("nan"))),
            )
        except Exception as exc:
            logger.warning("Sensitivity %s=%.6g failed: %s", variable_name, value, exc)
            point = SensitivityPoint(
                param_value=float(value),
                irr=float("nan"),
                npv=float("nan"),
                dscr_min=float("nan"),
                equity_irr=float("nan"),
            )

        points.append(point)

    return sorted(points, key=lambda p: p.param_value)


def run_full_sensitivity(
    base_params: dict[str, Any],
    steps: int = 7,
    variable_names: list[str] | None = None,
) -> dict[str, list[SensitivityPoint]]:
    """
    Run a sensitivity sweep for all 9 standard variables (or a custom subset).

    Each variable is swept independently while all others are held at their
    base values.  This mirrors the ``Scenarios!A17–N35`` sensitivity matrix
    in the Excel model.

    Args:
        base_params: See ``run_sensitivity`` for required keys.
        steps: Test points per variable (default 7).
        variable_names: Optional list of variable names to sweep.  Defaults
            to all 9 standard variables (``STANDARD_VARIABLE_NAMES``).

    Returns:
        Dict mapping variable name → list of ``SensitivityPoint`` results.
        Use ``build_sensitivity_dataframe`` to convert to a DataFrame.

    Example::

        full = run_full_sensitivity({"excel_path": "project.xlsx"})
        df = build_sensitivity_dataframe(full)
        plot_tornado_chart(df, "outputs/sensitivity_tornado.png")
    """
    if variable_names is None:
        variable_names = STANDARD_VARIABLE_NAMES

    results: dict[str, list[SensitivityPoint]] = {}
    for var in variable_names:
        logger.info("Full sensitivity: sweeping %s", var)
        results[var] = run_sensitivity(base_params, var, steps=steps)

    return results


# ---------------------------------------------------------------------------
# DataFrame builder
# ---------------------------------------------------------------------------


def build_sensitivity_dataframe(
    full_results: dict[str, list[SensitivityPoint]],
) -> pd.DataFrame:
    """
    Convert ``run_full_sensitivity`` output into a tidy DataFrame.

    Each row represents one (variable, param_value) scenario.  Columns
    also include pre-computed summary statistics useful for tornado charts:
    ``irr_range`` (max IRR – min IRR for the variable),
    ``npv_range``, and ``dscr_min_range``.

    Args:
        full_results: Output of ``run_full_sensitivity``.

    Returns:
        DataFrame with columns:
            ``variable_name``, ``display_name``, ``param_value``,
            ``irr``, ``npv_usd``, ``dscr_min``, ``equity_irr``,
            ``irr_range``, ``npv_range``, ``dscr_min_range``.

    Example::

        df = build_sensitivity_dataframe(full)
        # Rows sorted by irr_range descending (widest bar first)
        top = df.drop_duplicates("variable_name").sort_values(
            "irr_range", ascending=False
        )
    """
    rows: list[dict[str, Any]] = []
    for var_name, points in full_results.items():
        cfg = SENSITIVITY_VARIABLES.get(var_name)
        display = cfg.display_name if cfg else var_name

        irr_vals = [p.irr for p in points if not np.isnan(p.irr)]
        npv_vals = [p.npv for p in points if not np.isnan(p.npv)]
        dscr_vals = [p.dscr_min for p in points if not np.isnan(p.dscr_min)]

        irr_range = max(irr_vals) - min(irr_vals) if len(irr_vals) >= 2 else float("nan")
        npv_range = max(npv_vals) - min(npv_vals) if len(npv_vals) >= 2 else float("nan")
        dscr_range = max(dscr_vals) - min(dscr_vals) if len(dscr_vals) >= 2 else float("nan")

        for pt in points:
            rows.append(
                {
                    "variable_name": var_name,
                    "display_name": display,
                    "param_value": pt.param_value,
                    "irr": pt.irr,
                    "npv_usd": pt.npv,
                    "dscr_min": pt.dscr_min,
                    "equity_irr": pt.equity_irr,
                    "irr_range": irr_range,
                    "npv_range": npv_range,
                    "dscr_min_range": dscr_range,
                }
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tornado chart
# ---------------------------------------------------------------------------


def plot_tornado_chart(
    df: pd.DataFrame,
    output_path: str | Path = "outputs/sensitivity_tornado.png",
    metric: str = "irr",
    base_params: dict[str, Any] | None = None,
    figsize: tuple[float, float] = (10.0, 7.0),
    dpi: int = 150,
) -> Path:
    """
    Render a horizontal-bar tornado chart and save to *output_path*.

    The chart shows, for each sensitivity variable, the range of the chosen
    *metric* around its base-case value.  Variables are sorted by impact
    range (widest bar at the top).

    Args:
        df: DataFrame produced by ``build_sensitivity_dataframe``.
        output_path: File path for the saved PNG (created if necessary).
        metric: Column name to plot.  One of ``"irr"``, ``"npv_usd"``,
            ``"dscr_min"``, or ``"equity_irr"``.  Default ``"irr"``.
        base_params: Optional dict; if it contains the param_key values
            the base-case metric is annotated as a vertical dashed line.
            If ``None`` the median value across test points is used.
        figsize: Matplotlib figure size ``(width_inches, height_inches)``.
        dpi: Image resolution.

    Returns:
        ``Path`` to the saved PNG file.

    Raises:
        ImportError: If matplotlib is not installed.
        KeyError: If *metric* is not a column of *df*.

    Example::

        df = build_sensitivity_dataframe(full)
        path = plot_tornado_chart(df, "outputs/sensitivity_tornado.png")
        print(f"Chart saved to {path}")
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "matplotlib is required for plot_tornado_chart. Install it with: pip install matplotlib"
        ) from exc

    if metric not in df.columns:
        raise KeyError(
            f"Column {metric!r} not found in DataFrame. Available: {df.columns.tolist()}"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if metric.endswith("_range"):
        summary = df.groupby("variable_name", as_index=False).agg(range=(metric, "first"))
        summary["min"] = -summary["range"] / 2.0
        summary["max"] = summary["range"] / 2.0
        summary["median"] = 0.0
    else:
        # Summarise per variable: min, max of the metric
        summary = df.groupby("variable_name")[metric].agg(["min", "max", "median"]).reset_index()
        summary["range"] = summary["max"] - summary["min"]
    summary = summary.sort_values("range", ascending=True)  # bottom = smallest

    # Use display names on the y-axis
    display_map = (
        df[["variable_name", "display_name"]]
        .drop_duplicates("variable_name")
        .set_index("variable_name")["display_name"]
    )
    summary["label"] = summary["variable_name"].map(display_map).fillna(summary["variable_name"])

    # Determine base reference value (median across all test points per variable)
    base_val_map = summary.set_index("variable_name")["median"]

    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(len(summary))
    colors_left = "#d73027"  # below base — red
    colors_right = "#1a9850"  # above base — green

    for i, (_, row) in enumerate(summary.iterrows()):
        base_val = base_val_map[row["variable_name"]]
        low = row["min"] - base_val
        high = row["max"] - base_val

        # Left bar (below base)
        ax.barh(
            y_pos[i],
            low,
            left=base_val,
            height=0.6,
            color=colors_left,
            alpha=0.85,
            label="Below base" if i == 0 else "",
        )
        # Right bar (above base)
        ax.barh(
            y_pos[i],
            high,
            left=base_val,
            height=0.6,
            color=colors_right,
            alpha=0.85,
            label="Above base" if i == 0 else "",
        )

    # Vertical reference line at the base value of the first variable
    # (they all share the same metric baseline)
    global_base = float(summary["median"].median())
    ax.axvline(global_base, color="black", linewidth=1.2, linestyle="--", alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(summary["label"].tolist(), fontsize=9)

    metric_label = {
        "irr": "Project IRR",
        "equity_irr": "Equity IRR",
        "npv_usd": "NPV (USD)",
        "dscr_min": "Min DSCR",
        "irr_range": "Project IRR Range",
        "npv_range": "NPV Range (USD)",
        "dscr_min_range": "Min DSCR Range",
    }.get(metric, metric)

    # Format x-axis as percentage for IRR metrics
    if "irr" in metric.lower():
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=1))
    elif metric == "npv_usd":
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    ax.set_xlabel(metric_label, fontsize=10)
    ax.set_title(
        f"Sensitivity Tornado — {metric_label}\n"
        "(variables sorted by impact range; widest = most sensitive)",
        fontsize=11,
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    logger.info("Tornado chart saved to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Backward-compatible lower-level helper (original public API)
# ---------------------------------------------------------------------------


def run_sensitivity_for_values(
    variable_name: str,
    test_values: list[float],
    project_dir: Path | None = None,
    excel_path: Path | None = None,
    base_params: dict[str, Any] | None = None,
    ppa_option: int = 3,
    dppa_topology: str = "onsite",
    tariff_mode: str = "1-component",
) -> dict[float, dict[str, Any]]:
    """
    Run the full pipeline for each value of a single sensitivity variable.

    This is the original lower-level API retained for backward compatibility
    and advanced use-cases where the caller supplies explicit test values.

    One of *project_dir* (JSON+CSV) or *excel_path* must be provided.

    Excel source: Scenarios!A17–N35

    Args:
        variable_name: Name of variable to sweep.  Must be one of
            ``SENSITIVITY_VARIABLES`` keys or a direct financial_params key.
        test_values: List of values to test for the variable.
        project_dir: Path to directory with one JSON + one CSV file.
        excel_path: Path to Excel input file.
        base_params: Optional base parameter overrides (applied before sweep).
        ppa_option: PPA option to use for all runs (default 3 = DPPA).

    Returns:
        Dict mapping ``{test_value: kpi_dict}`` for each test value.

    Raises:
        ValueError: If neither *project_dir* nor *excel_path* is provided.
    """
    from re_storage.pipeline import run_full_model, run_model_from_json

    if dppa_topology not in {"onsite", "offsite"}:
        raise ValueError(f"dppa_topology must be 'onsite' or 'offsite', got {dppa_topology!r}")

    if project_dir is None and excel_path is None:
        raise ValueError("Either project_dir or excel_path must be provided.")

    # Resolve variable key
    if variable_name in SENSITIVITY_VARIABLES:
        param_key = SENSITIVITY_VARIABLES[variable_name].param_key
    else:
        param_key = variable_name

    results: dict[float, dict[str, Any]] = {}
    for value in test_values:
        logger.info("Sensitivity: %s = %s", variable_name, value)
        params = copy.deepcopy(base_params or {})
        params[param_key] = value

        try:
            if excel_path is not None:
                kpis = run_full_model(
                    Path(excel_path),
                    ppa_option=ppa_option,
                    base_params=params,
                    dppa_topology=dppa_topology,
                    tariff_mode=tariff_mode,
                )
            else:
                kpis = run_model_from_json(
                    Path(project_dir),
                    dppa_topology=dppa_topology,
                    ppa_option=ppa_option,
                    base_params=params,
                    tariff_mode=tariff_mode,
                )
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


# ---------------------------------------------------------------------------
# Categorical sensitivity: tariff mode (1-component vs 2-component)
# ---------------------------------------------------------------------------

#: KPIs reported in the tariff-mode delta.
_TARIFF_DELTA_KEYS = (
    "project_irr",
    "equity_irr",
    "npv_usd",
    "dscr_min",
    "year1_grid_savings_usd",
    "demand_charge_savings_usd",
)


def run_tariff_mode_comparison(
    project_dir: Path | None = None,
    excel_path: Path | None = None,
    base_params: dict[str, Any] | None = None,
    ppa_option: int = 3,
    dppa_topology: str = "onsite",
) -> dict[str, dict[str, Any]]:
    """
    Run the pipeline under both tariff modes and report the delta.

    Unlike the numeric sweeps, ``tariff_mode`` is a categorical variable, so
    this runs the full pipeline exactly twice — once as ``"1-component"`` and
    once as ``"2-component"`` — holding everything else fixed.  Two-component
    rates (Ca + Cp) are auto-loaded from the project inputs (Sprint 4 PHASE-02).

    One of *project_dir* (JSON+CSV) or *excel_path* must be provided.

    Returns:
        ``{"1-component": kpis, "2-component": kpis, "delta": {...}}`` where
        ``delta`` is ``2-component minus 1-component`` for the headline KPIs.
        A mode that errors stores ``{"error": ...}`` and is skipped in the delta.
    """
    from re_storage.pipeline import run_full_model, run_model_from_json

    if dppa_topology not in {"onsite", "offsite"}:
        raise ValueError(f"dppa_topology must be 'onsite' or 'offsite', got {dppa_topology!r}")
    if project_dir is None and excel_path is None:
        raise ValueError("Either project_dir or excel_path must be provided.")

    results: dict[str, dict[str, Any]] = {}
    for mode in ("1-component", "2-component"):
        logger.info("Tariff-mode comparison: %s", mode)
        try:
            if excel_path is not None:
                kpis = run_full_model(
                    Path(excel_path),
                    ppa_option=ppa_option,
                    base_params=copy.deepcopy(base_params or {}),
                    dppa_topology=dppa_topology,
                    tariff_mode=mode,
                )
            else:
                kpis = run_model_from_json(
                    Path(project_dir),
                    ppa_option=ppa_option,
                    base_params=copy.deepcopy(base_params or {}),
                    dppa_topology=dppa_topology,
                    tariff_mode=mode,
                )
            results[mode] = dict(kpis)
        except Exception as exc:
            logger.warning("Tariff-mode %s failed: %s", mode, exc)
            results[mode] = {"error": str(exc)}

    one = results.get("1-component", {})
    two = results.get("2-component", {})
    delta: dict[str, Any] = {}
    for key in _TARIFF_DELTA_KEYS:
        a = one.get(key)
        b = two.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            delta[key] = float(b) - float(a)
    results["delta"] = delta

    return results
