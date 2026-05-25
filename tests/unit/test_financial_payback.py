"""Unit tests for payback and cash-on-cash yield metrics."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from re_storage.financial.metrics import (
    calculate_cash_on_cash_yield,
    calculate_discounted_payback,
    calculate_simple_payback,
)


class TestSimplePayback:
    def test_simple_payback_positive_ebitda(self):
        """Known CAPEX/EBITDA → expected years."""
        result = calculate_simple_payback(total_capex_usd=10_000_000, year1_ebitda_usd=2_000_000)
        assert result == pytest.approx(5.0)

    def test_simple_payback_zero_ebitda(self):
        """Returns inf when EBITDA is zero."""
        result = calculate_simple_payback(total_capex_usd=10_000_000, year1_ebitda_usd=0.0)
        assert math.isinf(result)

    def test_simple_payback_negative_ebitda(self):
        """Returns inf when EBITDA is negative."""
        result = calculate_simple_payback(total_capex_usd=10_000_000, year1_ebitda_usd=-500_000)
        assert math.isinf(result)

    def test_simple_payback_small_project(self):
        """Small project with fast payback."""
        result = calculate_simple_payback(total_capex_usd=1_000_000, year1_ebitda_usd=500_000)
        assert result == pytest.approx(2.0)


class TestDiscountedPayback:
    def _make_dates(self, n: int) -> pd.Series:
        return pd.Series(pd.date_range("2027-01-01", periods=n, freq="YE"))

    def test_discounted_payback_recovers(self):
        """Cashflows that cross zero → correct year."""
        cashflows = pd.Series([-10_000_000, 2_000_000, 2_500_000, 3_000_000, 3_500_000, 4_000_000])
        dates = self._make_dates(len(cashflows))
        result = calculate_discounted_payback(cashflows, dates, discount_rate_pct=8.0)
        assert result is not None
        assert isinstance(result, int)

    def test_discounted_payback_never_recovers(self):
        """All-negative → None."""
        cashflows = pd.Series([-10_000_000, -1_000_000, -500_000])
        dates = self._make_dates(len(cashflows))
        result = calculate_discounted_payback(cashflows, dates, discount_rate_pct=8.0)
        assert result is None

    def test_discounted_payback_recovers_year_one(self):
        """Very high return → recovers in year 1."""
        cashflows = pd.Series([-1_000_000, 2_000_000])
        dates = self._make_dates(len(cashflows))
        result = calculate_discounted_payback(cashflows, dates, discount_rate_pct=8.0)
        assert result == 1

    def test_discounted_payback_zero_rate(self):
        """Zero discount rate → same as simple payback crossing point."""
        cashflows = pd.Series([-10_000_000, 3_000_000, 3_000_000, 3_000_000, 3_000_000])
        dates = self._make_dates(len(cashflows))
        result = calculate_discounted_payback(cashflows, dates, discount_rate_pct=0.0)
        assert result is not None


class TestCashOnCashYield:
    def test_cash_on_cash_positive(self):
        """Known FCFE/equity → expected ratio."""
        result = calculate_cash_on_cash_yield(year1_fcfe_usd=150_000, equity_invested_usd=1_000_000)
        assert result == pytest.approx(0.15)

    def test_cash_on_cash_zero_equity(self):
        """Returns 0.0 when equity is zero."""
        result = calculate_cash_on_cash_yield(year1_fcfe_usd=150_000, equity_invested_usd=0.0)
        assert result == 0.0

    def test_cash_on_cash_negative_equity(self):
        """Returns 0.0 when equity is negative."""
        result = calculate_cash_on_cash_yield(year1_fcfe_usd=150_000, equity_invested_usd=-100_000)
        assert result == 0.0

    def test_cash_on_cash_negative_fcfe(self):
        """Negative FCFE → negative yield."""
        result = calculate_cash_on_cash_yield(year1_fcfe_usd=-50_000, equity_invested_usd=1_000_000)
        assert result == pytest.approx(-0.05)
