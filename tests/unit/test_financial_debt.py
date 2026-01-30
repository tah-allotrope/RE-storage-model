"""
Unit tests for financial.debt module.

Tests cover:
1. Amortization schedule calculation.
2. Debt sizing for DSCR success path.
3. DSCR constraint failure when EBITDA is non-positive.
"""

from __future__ import annotations

import pandas as pd
import pytest

from re_storage.core.exceptions import DSCRConstraintError
from re_storage.financial.debt import calculate_amortization_schedule, size_debt_for_dscr


class TestAmortizationSchedule:
    """Tests for calculate_amortization_schedule."""

    def test_amortization_schedule_values(self) -> None:
        schedule = calculate_amortization_schedule(
            debt_amount_usd=1000.0, interest_rate_pct=10.0, tenor_years=2
        )

        assert schedule.loc[1, "opening_balance_usd"] == pytest.approx(1000.0)
        assert schedule.loc[1, "interest_usd"] == pytest.approx(100.0)
        assert schedule.loc[1, "principal_usd"] == pytest.approx(476.190476, rel=1e-4)
        assert schedule.loc[2, "closing_balance_usd"] == pytest.approx(0.0, abs=1e-6)
        assert schedule.loc[1, "total_debt_service_usd"] == pytest.approx(
            schedule.loc[2, "total_debt_service_usd"], rel=1e-6
        )


class TestDebtSizing:
    """Tests for size_debt_for_dscr."""

    def test_size_debt_for_dscr(self) -> None:
        ebitda = pd.Series([1300.0, 1200.0], index=[1, 2], name="ebitda_usd")
        debt_amount, schedule = size_debt_for_dscr(
            ebitda_series=ebitda,
            interest_rate_pct=10.0,
            tenor_years=2,
            target_dscr=1.3,
            initial_guess_usd=1000.0,
        )

        dscr = ebitda / schedule["total_debt_service_usd"]
        assert debt_amount > 0
        assert dscr.min() >= 1.3 - 1e-6

    def test_non_positive_ebitda_raises(self) -> None:
        ebitda = pd.Series([-10.0, 20.0], index=[1, 2], name="ebitda_usd")
        with pytest.raises(DSCRConstraintError, match="EBITDA"):
            size_debt_for_dscr(
                ebitda_series=ebitda,
                interest_rate_pct=10.0,
                tenor_years=2,
                target_dscr=1.3,
                initial_guess_usd=1000.0,
            )
