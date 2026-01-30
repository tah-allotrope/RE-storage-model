"""
Return metric calculations for project finance analysis.

Implements XNPV/XIRR-style functions and DSCR series to mirror Excel outputs
with explicit validation for cashflow sign and date alignment.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from re_storage.core.exceptions import InputValidationError


def _prepare_cashflows(
    cashflows: pd.Series, dates: pd.Series, label: str
) -> tuple[np.ndarray, np.ndarray]:
    if len(cashflows) != len(dates):
        raise InputValidationError(
            f"{label} cashflows and dates must have the same length.",
            field=label,
        )

    cashflow_values = pd.Series(cashflows, dtype=float)
    date_values = pd.to_datetime(pd.Series(dates), errors="coerce")
    if date_values.isna().any():
        raise InputValidationError(f"{label} dates contain invalid timestamps.")

    if not (cashflow_values.gt(0).any() and cashflow_values.lt(0).any()):
        raise InputValidationError(
            f"{label} cashflows must include at least one positive and one negative value."
        )

    base_date = date_values.iloc[0]
    year_fractions = (date_values - base_date).dt.days.to_numpy(dtype=float) / 365.0
    return cashflow_values.to_numpy(dtype=float), year_fractions


def _xnpv(rate: float, cashflows: np.ndarray, year_fractions: np.ndarray) -> float:
    return float(np.sum(cashflows / (1 + rate) ** year_fractions))


def _solve_irr(
    cashflows: np.ndarray, year_fractions: np.ndarray, label: str
) -> float:
    def npv_at(rate: float) -> float:
        return _xnpv(rate, cashflows, year_fractions)

    lower = -0.9999
    upper = 1.0
    lower_value = npv_at(lower)
    upper_value = npv_at(upper)

    attempts = 0
    while lower_value * upper_value > 0 and upper < 1000:
        upper *= 2
        upper_value = npv_at(upper)
        attempts += 1
        if attempts > 50:
            break

    if lower_value * upper_value > 0:
        raise InputValidationError(
            f"{label} IRR could not be bracketed for root finding.",
            field=label,
        )

    return float(brentq(npv_at, lower, upper))


def calculate_npv(
    cashflows: pd.Series, dates: pd.Series, discount_rate_pct: float
) -> float:
    """
    Calculate XNPV-style net present value.

    Args:
        cashflows: Cashflow series (USD).
        dates: Corresponding dates for each cashflow.
        discount_rate_pct: Discount rate as a percentage (e.g., 8.0).

    Returns:
        Net present value (USD).

    Raises:
        InputValidationError: If inputs are invalid.
    """
    if discount_rate_pct <= -100:
        raise InputValidationError("discount_rate_pct must be greater than -100.")

    cashflow_values, year_fractions = _prepare_cashflows(cashflows, dates, "npv")
    rate = discount_rate_pct / 100.0
    return _xnpv(rate, cashflow_values, year_fractions)


def calculate_project_irr(cashflows: pd.Series, dates: pd.Series) -> float:
    """
    Calculate project IRR using XIRR-style root finding.

    Args:
        cashflows: Project cashflow series (USD).
        dates: Corresponding dates for each cashflow.

    Returns:
        Project IRR as a decimal (e.g., 0.0507).

    Raises:
        InputValidationError: If inputs are invalid or IRR cannot be solved.
    """
    cashflow_values, year_fractions = _prepare_cashflows(cashflows, dates, "project")
    return _solve_irr(cashflow_values, year_fractions, "project")


def calculate_equity_irr(equity_cashflows: pd.Series, dates: pd.Series) -> float:
    """
    Calculate equity IRR using XIRR-style root finding.

    Args:
        equity_cashflows: Equity cashflow series (USD).
        dates: Corresponding dates for each cashflow.

    Returns:
        Equity IRR as a decimal.

    Raises:
        InputValidationError: If inputs are invalid or IRR cannot be solved.
    """
    cashflow_values, year_fractions = _prepare_cashflows(
        equity_cashflows, dates, "equity"
    )
    return _solve_irr(cashflow_values, year_fractions, "equity")


def calculate_dscr_series(ebitda_usd: pd.Series, debt_service_usd: pd.Series) -> pd.Series:
    """
    Calculate DSCR series from EBITDA and total debt service.

    Args:
        ebitda_usd: Annual EBITDA values (USD).
        debt_service_usd: Annual total debt service (USD).

    Returns:
        Series of DSCR values (ratio).

    Raises:
        InputValidationError: If inputs are invalid or debt service <= 0.
    """
    if not ebitda_usd.index.equals(debt_service_usd.index):
        raise InputValidationError("ebitda_usd and debt_service_usd indices must align.")

    if (debt_service_usd <= 0).any():
        raise InputValidationError("debt_service_usd must be positive.")

    dscr = ebitda_usd.astype(float) / debt_service_usd.astype(float)
    dscr.name = "dscr_ratio"
    return dscr
