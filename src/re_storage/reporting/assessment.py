"""Go/no-go assessment logic for DPPA project KPIs.

Interprets financial KPIs against configurable hurdle rates and returns
a structured verdict with human-readable explanations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class AssessmentThresholds:
    """Configurable thresholds for go/no-go assessment."""

    equity_irr_hurdle: float = 0.12
    dscr_covenant: float = 1.2
    max_payback_years: float = 15.0
    npv_floor_usd: float = 0.0


@dataclass
class AssessmentVerdict:
    """Structured verdict from assess_project()."""

    overall: str  # "GO" | "CAUTION" | "NO-GO"
    equity_irr_status: str  # "PASS" | "MARGINAL" | "FAIL"
    dscr_status: str
    npv_status: str
    payback_status: str
    details: list[str] = field(default_factory=list)


def _safe_float(value: float | None) -> float:
    """Return a float or NaN if value is None or not numeric."""
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _assess_metric(
    value: float,
    threshold: float,
    marginal_fraction: float = 0.8,
    higher_is_better: bool = True,
) -> tuple[str, str]:
    """Assess a single metric against a threshold.

    Returns (status, detail) where status is PASS, MARGINAL, or FAIL.
    """
    if math.isnan(value):
        return "FAIL", "value is missing or invalid"

    if higher_is_better:
        if value >= threshold:
            return "PASS", f"{value:.2%} meets threshold ({threshold:.2%})"
        if value >= threshold * marginal_fraction:
            return "MARGINAL", f"{value:.2%} is below threshold ({threshold:.2%}) but within marginal band"
        return "FAIL", f"{value:.2%} is below threshold ({threshold:.2%})"
    else:
        if value <= threshold:
            return "PASS", f"{value:.1f} meets threshold ({threshold:.1f})"
        if value <= threshold * (1.0 + (1.0 - marginal_fraction)):
            return "MARGINAL", f"{value:.1f} exceeds threshold ({threshold:.1f}) but within marginal band"
        return "FAIL", f"{value:.1f} exceeds threshold ({threshold:.1f})"


def assess_project(
    kpis: dict[str, float | None],
    thresholds: AssessmentThresholds | None = None,
) -> AssessmentVerdict:
    """Assess project KPIs against thresholds and return a verdict.

    Args:
        kpis: Dictionary of KPI values. Expected keys:
            - equity_irr (float)
            - dscr_min (float)
            - npv_usd (float)
            - simple_payback_years (float)
        thresholds: AssessmentThresholds instance. Uses defaults if None.

    Returns:
        AssessmentVerdict with overall status and per-metric details.
    """
    if thresholds is None:
        thresholds = AssessmentThresholds()

    equity_irr = _safe_float(kpis.get("equity_irr"))
    dscr_min = _safe_float(kpis.get("dscr_min"))
    npv_usd = _safe_float(kpis.get("npv_usd"))
    payback = _safe_float(kpis.get("simple_payback_years"))

    # Equity IRR: higher is better
    irr_status, irr_detail = _assess_metric(
        equity_irr, thresholds.equity_irr_hurdle, marginal_fraction=0.8, higher_is_better=True
    )

    # DSCR: higher is better
    dscr_status, dscr_detail = _assess_metric(
        dscr_min, thresholds.dscr_covenant, marginal_fraction=0.9, higher_is_better=True
    )

    # NPV: higher is better (floor is 0 by default)
    # Marginal band: -5% of capex (approximated as npv >= -capex * 0.05)
    # For simplicity, use floor * 0.8 as marginal band when floor is 0
    npv_status = "FAIL"
    npv_detail = ""
    if math.isnan(npv_usd):
        npv_status = "FAIL"
        npv_detail = "NPV is missing or invalid"
    elif npv_usd >= thresholds.npv_floor_usd:
        npv_status = "PASS"
        npv_detail = f"NPV ${npv_usd:,.0f} meets floor (${thresholds.npv_floor_usd:,.0f})"
    elif npv_usd >= thresholds.npv_floor_usd - 1_000_000:
        npv_status = "MARGINAL"
        npv_detail = f"NPV ${npv_usd:,.0f} is below floor but within marginal band"
    else:
        npv_status = "FAIL"
        npv_detail = f"NPV ${npv_usd:,.0f} is below floor (${thresholds.npv_floor_usd:,.0f})"

    # Payback: lower is better
    payback_status, payback_detail = _assess_metric(
        payback, thresholds.max_payback_years, marginal_fraction=0.8333, higher_is_better=False
    )
    # Adjust detail message for payback
    if payback_status == "PASS":
        payback_detail = f"{payback:.1f} years meets max ({thresholds.max_payback_years:.1f} years)"
    elif payback_status == "MARGINAL":
        payback_detail = f"{payback:.1f} years exceeds max ({thresholds.max_payback_years:.1f} years) but within marginal band"
    else:
        payback_detail = f"{payback:.1f} years exceeds max ({thresholds.max_payback_years:.1f} years)"

    # Determine overall verdict
    statuses = [irr_status, dscr_status, npv_status, payback_status]
    if all(s == "PASS" for s in statuses):
        overall = "GO"
    elif any(s == "FAIL" for s in statuses):
        overall = "NO-GO"
    else:
        overall = "CAUTION"

    details = [
        f"Equity IRR: {irr_status} — {irr_detail}",
        f"Min DSCR: {dscr_status} — {dscr_detail}",
        f"NPV: {npv_status} — {npv_detail}",
        f"Simple Payback: {payback_status} — {payback_detail}",
    ]

    return AssessmentVerdict(
        overall=overall,
        equity_irr_status=irr_status,
        dscr_status=dscr_status,
        npv_status=npv_status,
        payback_status=payback_status,
        details=details,
    )
