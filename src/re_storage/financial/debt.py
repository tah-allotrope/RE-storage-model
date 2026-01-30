"""
Debt sizing and amortization utilities.

Provides amortization schedule construction and DSCR-based debt sizing
consistent with the Excel GoalSeek logic.
"""

from __future__ import annotations

import pandas as pd
from scipy.optimize import brentq

from re_storage.core.exceptions import DSCRConstraintError, InputValidationError
from re_storage.core.types import AnnualTimeSeries


def calculate_amortization_schedule(
    debt_amount_usd: float,
    interest_rate_pct: float,
    tenor_years: int,
) -> AnnualTimeSeries:
    """
    Calculate annual amortization schedule for a fixed-rate loan.

    Args:
        debt_amount_usd: Initial debt principal (USD).
        interest_rate_pct: Annual interest rate (percent).
        tenor_years: Repayment period (years).

    Returns:
        AnnualTimeSeries with principal, interest, and balances.

    Raises:
        InputValidationError: If inputs are invalid.
    """
    if debt_amount_usd <= 0:
        raise InputValidationError("debt_amount_usd must be positive.")
    if interest_rate_pct < 0:
        raise InputValidationError("interest_rate_pct must be non-negative.")
    if tenor_years <= 0:
        raise InputValidationError("tenor_years must be positive.")

    rate = interest_rate_pct / 100.0
    if rate == 0:
        payment_usd = debt_amount_usd / tenor_years
    else:
        payment_usd = debt_amount_usd * rate / (1 - (1 + rate) ** (-tenor_years))

    balance = debt_amount_usd
    rows: list[dict[str, float]] = []

    for year in range(1, tenor_years + 1):
        interest_usd = balance * rate
        principal_usd = payment_usd - interest_usd
        closing_balance_usd = balance - principal_usd
        if year == tenor_years:
            closing_balance_usd = 0.0
            principal_usd = balance
            payment_usd = interest_usd + principal_usd
        rows.append(
            {
                "year": float(year),
                "opening_balance_usd": balance,
                "interest_usd": interest_usd,
                "principal_usd": principal_usd,
                "total_debt_service_usd": payment_usd,
                "closing_balance_usd": closing_balance_usd,
            }
        )
        balance = closing_balance_usd

    schedule = pd.DataFrame(rows)
    schedule["year"] = schedule["year"].astype(int)
    return schedule.set_index("year", drop=False)


def size_debt_for_dscr(
    ebitda_series: pd.Series,
    interest_rate_pct: float,
    tenor_years: int,
    target_dscr: float,
    initial_guess_usd: float,
) -> tuple[float, AnnualTimeSeries]:
    """
    Find maximum debt size that satisfies DSCR covenant across tenor.

    Args:
        ebitda_series: Annual EBITDA values indexed by year (USD).
        interest_rate_pct: Annual interest rate (percent).
        tenor_years: Debt tenor (years).
        target_dscr: Minimum DSCR threshold.
        initial_guess_usd: Initial debt guess for bracketing (USD).

    Returns:
        Tuple of (optimal_debt_amount_usd, amortization_schedule).

    Raises:
        DSCRConstraintError: If DSCR constraint cannot be satisfied.
        InputValidationError: If inputs are invalid.
    """
    if target_dscr <= 0:
        raise InputValidationError("target_dscr must be positive.")
    if initial_guess_usd <= 0:
        raise InputValidationError("initial_guess_usd must be positive.")
    if interest_rate_pct < 0:
        raise InputValidationError("interest_rate_pct must be non-negative.")
    if tenor_years <= 0:
        raise InputValidationError("tenor_years must be positive.")

    years = pd.Index(range(1, tenor_years + 1))
    if not years.isin(ebitda_series.index).all():
        raise InputValidationError("ebitda_series must include all tenor years.")

    ebitda = ebitda_series.loc[years].astype(float)
    if (ebitda <= 0).any():
        raise DSCRConstraintError("EBITDA must be positive to size debt.")

    def min_dscr(debt_amount_usd: float) -> float:
        schedule = calculate_amortization_schedule(
            debt_amount_usd=debt_amount_usd,
            interest_rate_pct=interest_rate_pct,
            tenor_years=tenor_years,
        )
        dscr = ebitda / schedule["total_debt_service_usd"]
        return float(dscr.min())

    def dscr_residual(debt_amount_usd: float) -> float:
        return min_dscr(debt_amount_usd) - target_dscr

    lower = 1e-6
    upper = initial_guess_usd

    residual_lower = dscr_residual(lower)
    if residual_lower < 0:
        raise DSCRConstraintError(
            "EBITDA too low to meet DSCR even at minimal debt.",
            min_dscr_achieved=residual_lower + target_dscr,
            target_dscr=target_dscr,
        )

    residual_upper = dscr_residual(upper)
    attempts = 0
    while residual_upper > 0 and attempts < 20:
        upper *= 2
        residual_upper = dscr_residual(upper)
        attempts += 1

    if residual_upper > 0:
        raise DSCRConstraintError(
            "Unable to bracket DSCR target with initial_guess_usd.",
            min_dscr_achieved=residual_upper + target_dscr,
            target_dscr=target_dscr,
        )

    optimal_debt_usd = float(brentq(dscr_residual, lower, upper))
    schedule = calculate_amortization_schedule(
        debt_amount_usd=optimal_debt_usd,
        interest_rate_pct=interest_rate_pct,
        tenor_years=tenor_years,
    )

    return optimal_debt_usd, schedule
