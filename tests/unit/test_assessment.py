"""Unit tests for the go/no-go assessment module."""

from __future__ import annotations

import math

import pytest

from re_storage.reporting.assessment import (
    AssessmentThresholds,
    AssessmentVerdict,
    assess_project,
)


def _strong_kpis() -> dict[str, float]:
    return {
        "equity_irr": 0.15,
        "dscr_min": 1.5,
        "npv_usd": 1_000_000.0,
        "simple_payback_years": 8.0,
    }


class TestAssessProject:
    def test_all_pass_returns_go(self):
        verdict = assess_project(_strong_kpis())
        assert verdict.overall == "GO"
        assert verdict.equity_irr_status == "PASS"
        assert verdict.dscr_status == "PASS"
        assert verdict.npv_status == "PASS"
        assert verdict.payback_status == "PASS"

    def test_one_fail_returns_nogo(self):
        kpis = _strong_kpis()
        kpis["equity_irr"] = 0.05  # Well below 12% hurdle
        verdict = assess_project(kpis)
        assert verdict.overall == "NO-GO"
        assert verdict.equity_irr_status == "FAIL"

    def test_marginal_returns_caution(self):
        kpis = _strong_kpis()
        kpis["equity_irr"] = 0.10  # 0.8 * 0.12 = 0.096, so 0.10 is MARGINAL
        verdict = assess_project(kpis)
        assert verdict.overall == "CAUTION"
        assert verdict.equity_irr_status == "MARGINAL"

    def test_nan_irr_returns_nogo(self):
        kpis = _strong_kpis()
        kpis["equity_irr"] = float("nan")
        verdict = assess_project(kpis)
        assert verdict.overall == "NO-GO"
        assert verdict.equity_irr_status == "FAIL"
        assert any("missing" in d.lower() for d in verdict.details)

    def test_custom_thresholds(self):
        kpis = _strong_kpis()
        thresholds = AssessmentThresholds(
            equity_irr_hurdle=0.20,
            dscr_covenant=1.5,
            max_payback_years=5.0,
        )
        verdict = assess_project(kpis, thresholds=thresholds)
        # Equity IRR 0.15 < 0.20 hurdle → FAIL
        # DSCR 1.5 >= 1.5 → PASS
        # Payback 8.0 > 5.0 → FAIL
        assert verdict.overall == "NO-GO"
        assert verdict.equity_irr_status == "FAIL"
        assert verdict.dscr_status == "PASS"
        assert verdict.payback_status == "FAIL"

    def test_details_explain_each_verdict(self):
        verdict = assess_project(_strong_kpis())
        assert len(verdict.details) == 4
        assert any("Equity IRR" in d for d in verdict.details)
        assert any("Min DSCR" in d for d in verdict.details)
        assert any("NPV" in d for d in verdict.details)
        assert any("Simple Payback" in d for d in verdict.details)

    def test_none_values_treated_as_fail(self):
        kpis = {
            "equity_irr": None,
            "dscr_min": None,
            "npv_usd": None,
            "simple_payback_years": None,
        }
        verdict = assess_project(kpis)
        assert verdict.overall == "NO-GO"
        assert verdict.equity_irr_status == "FAIL"
        assert verdict.dscr_status == "FAIL"
        assert verdict.npv_status == "FAIL"
        assert verdict.payback_status == "FAIL"

    def test_payback_marginal_band(self):
        kpis = _strong_kpis()
        kpis["simple_payback_years"] = 16.0  # 15 * 1.2 = 18, so 16 is MARGINAL
        verdict = assess_project(kpis)
        assert verdict.overall == "CAUTION"
        assert verdict.payback_status == "MARGINAL"

    def test_npv_marginal_band(self):
        kpis = _strong_kpis()
        kpis["npv_usd"] = -500_000.0  # Within 1M of floor 0
        verdict = assess_project(kpis)
        assert verdict.overall == "CAUTION"
        assert verdict.npv_status == "MARGINAL"

    def test_npv_fail_band(self):
        kpis = _strong_kpis()
        kpis["npv_usd"] = -2_000_000.0  # Below 1M marginal band
        verdict = assess_project(kpis)
        assert verdict.overall == "NO-GO"
        assert verdict.npv_status == "FAIL"
