"""
Tax calculation utilities.

Implements corporate tax schedule with holiday and tiered discount periods,
straight-line depreciation, and after-tax FCF computation.

Excel source: Financial!F125–F150, Assumption!K44, K62–K65
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_tax_rate_schedule(
    project_years: int,
    tax_rate: float = 0.20,
    holiday_years: int = 5,
    first_discount_years: int = 8,
    first_discount_rate: float = 0.05,
    second_discount_years: int = 2,
    second_discount_rate: float = 0.10,
) -> pd.Series:
    """
    Build annual tax rate schedule with holiday and tiered discount periods.

    Excel source: Assumption!K62–K65, J64–J65

    Schedule:
        Years 1..holiday_years                                  → 0%
        Years (holiday+1)..(holiday+first_discount)            → first_discount_rate
        Years (holiday+first+1)..(holiday+first+second)        → second_discount_rate
        Years beyond                                            → tax_rate (standard)

    Args:
        project_years: Total project length in years.
        tax_rate: Standard corporate tax rate (K62, default 20%).
        holiday_years: Zero-tax holiday years (K63, default 5).
        first_discount_years: Years at first discount rate (J64, default 8).
        first_discount_rate: Rate during first discount period (K64, default 5%).
        second_discount_years: Years at second discount rate (J65, default 2).
        second_discount_rate: Rate during second discount period (K65, default 10%).

    Returns:
        Series of annual tax rates (fractions) indexed by year (1-based).
    """
    rates: list[float] = []
    for year in range(1, project_years + 1):
        if year <= holiday_years:
            rates.append(0.0)
        elif year <= holiday_years + first_discount_years:
            rates.append(first_discount_rate)
        elif year <= holiday_years + first_discount_years + second_discount_years:
            rates.append(second_discount_rate)
        else:
            rates.append(tax_rate)
    return pd.Series(rates, index=pd.RangeIndex(1, project_years + 1), name="tax_rate")


def calculate_depreciation_schedule(
    total_capex_usd: float,
    tenor_years: int,
    project_years: int,
) -> pd.Series:
    """
    Calculate straight-line depreciation schedule.

    Excel source: Assumption!K44 (Depreciation Tenor, default 20 yrs)

    Args:
        total_capex_usd: Total capital expenditure (USD).
        tenor_years: Depreciation tenor in years (e.g., 20).
        project_years: Project lifetime in years.

    Returns:
        Series of annual depreciation (USD) indexed by year (1-based).
        Zero after tenor_years.
    """
    annual_dep = total_capex_usd / tenor_years if tenor_years > 0 else 0.0
    depreciation = [
        annual_dep if year <= tenor_years else 0.0
        for year in range(1, project_years + 1)
    ]
    return pd.Series(
        depreciation,
        index=pd.RangeIndex(1, project_years + 1),
        name="depreciation_usd",
    )


def calculate_unlevered_taxes(
    ebitda: pd.Series,
    depreciation: pd.Series,
    tax_rates: pd.Series,
) -> pd.Series:
    """
    Calculate unlevered (project-level) taxes.

    EBIT = EBITDA - Depreciation
    Tax  = max(0, EBIT × tax_rate)

    Excel source: Financial!F132 (unlevered tax)

    Args:
        ebitda: Annual EBITDA series (USD), indexed by year.
        depreciation: Annual depreciation series (USD), indexed by year.
        tax_rates: Annual tax rate series (fractions), indexed by year.

    Returns:
        Series of unlevered tax amounts (USD), indexed by year.
    """
    ebit = ebitda.values - depreciation.values
    taxes = np.maximum(0.0, ebit * tax_rates.values)
    return pd.Series(taxes, index=ebitda.index, name="unlevered_taxes_usd")


def calculate_levered_taxes(
    ebitda: pd.Series,
    depreciation: pd.Series,
    debt_interest: pd.Series,
    tax_rates: pd.Series,
) -> pd.Series:
    """
    Calculate levered (equity-level) taxes after interest deduction.

    EBIT = EBITDA - Depreciation
    EBT  = EBIT - Interest
    Tax  = max(0, EBT × tax_rate)

    Excel source: Financial!F150 (levered tax)

    Args:
        ebitda: Annual EBITDA series (USD).
        depreciation: Annual depreciation series (USD).
        debt_interest: Annual debt interest payments (USD).
        tax_rates: Annual tax rate series (fractions).

    Returns:
        Series of levered tax amounts (USD), indexed by year.
    """
    ebit = ebitda.values - depreciation.values
    ebt = ebit - debt_interest.values
    taxes = np.maximum(0.0, ebt * tax_rates.values)
    return pd.Series(taxes, index=ebitda.index, name="levered_taxes_usd")
