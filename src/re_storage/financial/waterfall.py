"""
Cash flow waterfall construction.

Builds annual cash flow metrics (revenue → EBITDA → CFADS → equity) using
lifetime revenue, opex, and debt schedules.
"""

from __future__ import annotations

import pandas as pd

from re_storage.core.exceptions import InputValidationError
from re_storage.core.types import AnnualTimeSeries


REVENUE_COLUMNS = {
    "year",
    "dppa_revenue_usd",
    "grid_savings_usd",
    "demand_charge_savings_usd",
}
OPEX_COLUMNS = {
    "year",
    "o_and_m_usd",
    "insurance_usd",
    "land_lease_usd",
    "management_fees_usd",
    "grid_connection_usd",
    "taxes_usd",
    "mra_contribution_usd",
}
DEBT_COLUMNS = {
    "year",
    "interest_usd",
    "principal_usd",
    "total_debt_service_usd",
}


def _require_columns(data: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(data.columns)
    if missing:
        raise InputValidationError(
            f"Missing required columns in {label}: {sorted(missing)}"
        )


def _with_year_index(data: AnnualTimeSeries, label: str) -> AnnualTimeSeries:
    _require_columns(data, {"year"}, label)
    result = data.copy()
    return result.set_index("year", drop=False)


def build_cash_flow_waterfall(
    lifetime_revenue: AnnualTimeSeries,
    lifetime_opex: AnnualTimeSeries,
    debt_schedule: AnnualTimeSeries,
    capex: dict[str, float | pd.Series],
) -> AnnualTimeSeries:
    """
    Construct annual cash flow waterfall for project finance analysis.

    Args:
        lifetime_revenue: Annual revenue projection with unit-suffixed columns.
        lifetime_opex: Annual operating costs including taxes and MRA.
        debt_schedule: Annual debt service schedule.
        capex: Capex dictionary with required initial capex and optional augmentation.

    Returns:
        AnnualTimeSeries with waterfall metrics and capex line items.

    Raises:
        InputValidationError: If inputs are missing required data or invalid.
    """
    _require_columns(lifetime_revenue, REVENUE_COLUMNS, "lifetime_revenue")
    _require_columns(lifetime_opex, OPEX_COLUMNS, "lifetime_opex")
    _require_columns(debt_schedule, DEBT_COLUMNS, "debt_schedule")

    revenue = _with_year_index(lifetime_revenue, "lifetime_revenue")
    opex = _with_year_index(lifetime_opex, "lifetime_opex")
    debt = _with_year_index(debt_schedule, "debt_schedule")

    years = revenue.index
    if not years.equals(opex.index) or not years.equals(debt.index):
        raise InputValidationError("Year indices must align across revenue, opex, and debt.")

    if "initial_capex_usd" not in capex:
        raise InputValidationError("capex must include initial_capex_usd.")

    initial_capex_usd = float(capex["initial_capex_usd"])
    if initial_capex_usd < 0:
        raise InputValidationError("initial_capex_usd must be non-negative.")

    augmentation_capex = capex.get("augmentation_capex_usd")
    if augmentation_capex is None:
        augmentation_series = pd.Series(dtype=float)
    elif isinstance(augmentation_capex, pd.Series):
        augmentation_series = augmentation_capex.astype(float)
    else:
        raise InputValidationError("augmentation_capex_usd must be a pandas Series.")

    total_revenue_usd = (
        revenue["dppa_revenue_usd"]
        + revenue["grid_savings_usd"]
        + revenue["demand_charge_savings_usd"]
    )
    total_opex_usd = (
        opex["o_and_m_usd"]
        + opex["insurance_usd"]
        + opex["land_lease_usd"]
        + opex["management_fees_usd"]
        + opex["grid_connection_usd"]
    )
    ebitda_usd = total_revenue_usd - total_opex_usd
    cfads_usd = ebitda_usd - debt["total_debt_service_usd"]
    free_cash_flow_to_equity_usd = (
        cfads_usd - opex["taxes_usd"] - opex["mra_contribution_usd"]
    )

    output_years = pd.Index([0]).append(years)
    waterfall = pd.DataFrame(
        index=output_years,
        columns=[
            "year",
            "total_revenue_usd",
            "total_opex_usd",
            "ebitda_usd",
            "interest_usd",
            "principal_usd",
            "total_debt_service_usd",
            "cfads_usd",
            "taxes_usd",
            "mra_contribution_usd",
            "free_cash_flow_to_equity_usd",
            "capex_usd",
        ],
        data=0.0,
    )

    waterfall.loc[years, "total_revenue_usd"] = total_revenue_usd.values
    waterfall.loc[years, "total_opex_usd"] = total_opex_usd.values
    waterfall.loc[years, "ebitda_usd"] = ebitda_usd.values
    waterfall.loc[years, "interest_usd"] = debt["interest_usd"].values
    waterfall.loc[years, "principal_usd"] = debt["principal_usd"].values
    waterfall.loc[years, "total_debt_service_usd"] = debt["total_debt_service_usd"].values
    waterfall.loc[years, "cfads_usd"] = cfads_usd.values
    waterfall.loc[years, "taxes_usd"] = opex["taxes_usd"].values
    waterfall.loc[years, "mra_contribution_usd"] = opex["mra_contribution_usd"].values
    waterfall.loc[years, "free_cash_flow_to_equity_usd"] = free_cash_flow_to_equity_usd.values

    capex_usd = pd.Series(0.0, index=output_years)
    capex_usd.loc[0] = initial_capex_usd
    if not augmentation_series.empty:
        aligned = augmentation_series.reindex(output_years, fill_value=0.0)
        capex_usd = capex_usd.add(aligned, fill_value=0.0)
    waterfall["capex_usd"] = capex_usd.values
    waterfall["year"] = waterfall.index

    return waterfall
