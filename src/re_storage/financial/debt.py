"""
Debt sizing and amortization utilities.

Provides amortization schedule construction and DSCR-based debt sizing
consistent with the Excel GoalSeek logic.
"""

from __future__ import annotations

import pandas as pd

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

    target_debt_service = ebitda / target_dscr
    rate = interest_rate_pct / 100.0
    discount_factors = pd.Series(
        [(1.0 + rate) ** year for year in range(1, tenor_years + 1)],
        index=years,
        dtype=float,
    )
    optimal_debt_usd = float((target_debt_service / discount_factors).sum())
    schedule = calculate_sculpted_debt_schedule(
        debt_amount_usd=optimal_debt_usd,
        cfads_series=ebitda,
        interest_rate_pct=interest_rate_pct,
        target_dscr=target_dscr,
    )

    return optimal_debt_usd, schedule


def calculate_sculpted_debt_schedule(
    debt_amount_usd: float,
    cfads_series: pd.Series,
    interest_rate_pct: float,
    target_dscr: float,
) -> AnnualTimeSeries:
    """Build the workbook-style sculpted debt schedule from CFADS and DSCR."""
    if debt_amount_usd <= 0:
        raise InputValidationError("debt_amount_usd must be positive.")
    if interest_rate_pct < 0:
        raise InputValidationError("interest_rate_pct must be non-negative.")
    if target_dscr <= 0:
        raise InputValidationError("target_dscr must be positive.")

    cfads = cfads_series.astype(float)
    if cfads.empty:
        raise InputValidationError("cfads_series must not be empty.")
    if (cfads <= 0).any():
        raise DSCRConstraintError("CFADS must be positive to sculpt debt.")

    rate = interest_rate_pct / 100.0
    balance = float(debt_amount_usd)
    rows: list[dict[str, float]] = []

    for year, cfads_value in cfads.items():
        target_debt_service = float(cfads_value) / target_dscr
        interest_usd = balance * rate
        principal_usd = target_debt_service - interest_usd

        if principal_usd < -1e-9:
            raise DSCRConstraintError(
                "CFADS is too low to cover sculpted debt interest.",
                min_dscr_achieved=float(cfads_value / interest_usd) if interest_usd > 0 else None,
                target_dscr=target_dscr,
            )

        principal_usd = max(principal_usd, 0.0)
        if principal_usd > balance:
            principal_usd = balance

        total_debt_service_usd = interest_usd + principal_usd
        closing_balance_usd = balance - principal_usd
        if abs(closing_balance_usd) < 1e-6:
            closing_balance_usd = 0.0

        rows.append(
            {
                "year": int(year),
                "opening_balance_usd": balance,
                "interest_usd": interest_usd,
                "principal_usd": principal_usd,
                "total_debt_service_usd": total_debt_service_usd,
                "closing_balance_usd": closing_balance_usd,
            }
        )
        balance = closing_balance_usd

    schedule = pd.DataFrame(rows)
    schedule["year"] = schedule["year"].astype(int)
    return schedule.set_index("year", drop=False)
