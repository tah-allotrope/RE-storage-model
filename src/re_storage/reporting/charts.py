"""Dispatch chart generator for embedding matplotlib PNGs into Excel workbooks.

Produces 8x4 inch PNG charts using the Allotrope color palette and Calibri font
(falling back to sans-serif). All rendering is headless via matplotlib "Agg" backend.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Allotrope brand palette
# ---------------------------------------------------------------------------

BRAND_GREEN = "#2E7D32"
BRAND_BLUE = "#1565C0"
BRAND_GRAY = "#9E9E9E"
BRAND_YELLOW = "#F9A825"
BRAND_RED = "#C62828"
BRAND_DARK = "#212121"
BRAND_LIGHT = "#757575"

# ---------------------------------------------------------------------------
# Font setup
# ---------------------------------------------------------------------------


def _set_allotrope_font() -> None:
    """Set Calibri if available, otherwise sans-serif."""
    try:
        plt.rcParams["font.family"] = ["Calibri", "sans-serif"]
    except Exception:
        plt.rcParams["font.family"] = "sans-serif"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_fig_to_temp(fig: plt.Figure) -> Path:
    """Save a figure to a temporary PNG and return the path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return Path(path)


def _hour_of_day(hourly_df: pd.DataFrame) -> pd.Series:
    """Extract hour-of-day (0-23) from a DataFrame's index or columns."""
    if isinstance(hourly_df.index, pd.DatetimeIndex):
        return hourly_df.index.hour
    if "hour" in hourly_df.columns:
        return hourly_df["hour"]
    if "datetime" in hourly_df.columns:
        return pd.to_datetime(hourly_df["datetime"]).dt.hour
    # Fallback: assume 8760 rows = 365 days * 24 hours
    return pd.Series([i % 24 for i in range(len(hourly_df))], index=hourly_df.index)


# ---------------------------------------------------------------------------
# Public chart functions
# ---------------------------------------------------------------------------


def generate_average_day_dispatch(
    hourly_df: pd.DataFrame,
    title: str = "Average Day Dispatch",
) -> Path:
    """Generate a stacked area chart of average daily dispatch profiles.

    Stacks solar generation, battery discharge, and grid import to meet load.
    SoC is shown on a secondary y-axis.
    """
    _set_allotrope_font()
    hour = _hour_of_day(hourly_df)

    # Average each column by hour-of-day
    avg = hourly_df.groupby(hour).mean(numeric_only=True)

    # Resolve column names with fallbacks
    solar_col = next(
        (c for c in avg.columns if "solar_gen" in c or "solar" in c), None
    )
    load_col = next((c for c in avg.columns if "load_kw" in c), None)
    soc_col = next((c for c in avg.columns if "soc_kwh" in c or "soc" in c), None)
    discharge_col = next(
        (c for c in avg.columns if "discharged_kw" in c or "discharge" in c), None
    )
    charge_col = next(
        (c for c in avg.columns if "pv_charged_kw" in c or "charge" in c), None
    )
    grid_col = next(
        (c for c in avg.columns if "grid_load_after_re" in c or "grid" in c), None
    )

    fig, ax1 = plt.subplots(figsize=(8, 4))
    hours = avg.index

    # Stacked area: solar + discharge + grid
    solar = avg[solar_col] if solar_col in avg.columns else pd.Series(0, index=hours)
    discharge = (
        avg[discharge_col] if discharge_col in avg.columns else pd.Series(0, index=hours)
    )
    grid = avg[grid_col] if grid_col in avg.columns else pd.Series(0, index=hours)

    ax1.fill_between(hours, 0, solar, color=BRAND_YELLOW, alpha=0.7, label="Solar Gen")
    ax1.fill_between(
        hours, solar, solar + discharge, color=BRAND_BLUE, alpha=0.7, label="Battery Discharge"
    )
    ax1.fill_between(
        hours,
        solar + discharge,
        solar + discharge + grid,
        color=BRAND_GRAY,
        alpha=0.7,
        label="Grid Import",
    )

    # Load line
    if load_col in avg.columns:
        ax1.plot(hours, avg[load_col], color=BRAND_DARK, linewidth=2, label="Load")

    ax1.set_xlabel("Hour of Day")
    ax1.set_ylabel("Power (kW)")
    ax1.set_title(title, fontweight="bold", color=BRAND_DARK)
    ax1.set_xlim(0, 23)
    ax1.legend(loc="upper left", frameon=False)
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Secondary y-axis for SoC
    if soc_col in avg.columns:
        ax2 = ax1.twinx()
        ax2.plot(hours, avg[soc_col], color=BRAND_GREEN, linestyle="--", linewidth=2, label="SoC")
        ax2.set_ylabel("State of Charge (kWh)", color=BRAND_GREEN)
        ax2.tick_params(axis="y", labelcolor=BRAND_GREEN)
        ax2.legend(loc="upper right", frameon=False)

    plt.tight_layout()
    return _save_fig_to_temp(fig)


def generate_dscr_line_chart(
    annual_df: pd.DataFrame,
    covenant: float = 1.3,
    title: str = "DSCR Profile",
) -> Path:
    """Generate a line chart of DSCR over project years with covenant threshold."""
    _set_allotrope_font()

    dscr_col = next((c for c in annual_df.columns if "dscr" in c), None)
    year_col = next((c for c in annual_df.columns if c in ("year", "years")), None)

    if dscr_col is None:
        raise ValueError(" annual_df must contain a 'dscr' column")

    years = annual_df[year_col] if year_col else annual_df.index

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(years, annual_df[dscr_col], color=BRAND_BLUE, linewidth=2.5, marker="o", markersize=5)
    ax.axhline(
        covenant, color=BRAND_RED, linestyle="--", linewidth=1.5, label=f"Covenant ({covenant:.2f}x)"
    )

    # Shade area below covenant
    ax.fill_between(
        years,
        annual_df[dscr_col],
        covenant,
        where=(annual_df[dscr_col] < covenant),
        color=BRAND_RED,
        alpha=0.15,
        interpolate=True,
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("DSCR")
    ax.set_title(title, fontweight="bold", color=BRAND_DARK)
    ax.legend(loc="best", frameon=False)
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    return _save_fig_to_temp(fig)


def generate_monthly_generation_bar(
    annual_df: pd.DataFrame,
    title: str = "Annual Revenue Breakdown",
) -> Path:
    """Generate a stacked bar chart of annual revenue components.

    Stacks DPPA Revenue, Grid Savings, and Demand Charge Savings per year.
    """
    _set_allotrope_font()

    year_col = next((c for c in annual_df.columns if c in ("year", "years")), None)
    years = annual_df[year_col] if year_col else annual_df.index

    dppa_col = next(
        (c for c in annual_df.columns if "dppa_revenue" in c or "dppa" in c), None
    )
    grid_col = next(
        (c for c in annual_df.columns if "grid_savings" in c or "grid" in c), None
    )
    demand_col = next(
        (c for c in annual_df.columns if "demand_charge_savings" in c or "demand" in c), None
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    bar_width = 0.6

    bottom = pd.Series(0, index=years.index if hasattr(years, "index") else range(len(years)))
    x = range(len(years))

    if dppa_col:
        ax.bar(x, annual_df[dppa_col], bar_width, color=BRAND_YELLOW, label="DPPA Revenue")
        bottom = bottom.add(annual_df[dppa_col].values, fill_value=0)

    if grid_col:
        ax.bar(
            x,
            annual_df[grid_col],
            bar_width,
            bottom=bottom,
            color=BRAND_BLUE,
            label="Grid Savings",
        )
        bottom = bottom.add(annual_df[grid_col].values, fill_value=0)

    if demand_col:
        ax.bar(
            x,
            annual_df[demand_col],
            bar_width,
            bottom=bottom,
            color=BRAND_GREEN,
            label="Demand Charge Savings",
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("USD")
    ax.set_title(title, fontweight="bold", color=BRAND_DARK)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend(loc="best", frameon=False)
    ax.grid(True, linestyle="--", alpha=0.3, axis="y")

    plt.tight_layout()
    return _save_fig_to_temp(fig)
