"""
Financial layer for cash flow and return metrics.

This package assembles annual cash flow waterfalls, sizes debt to DSCR
constraints, and computes IRR/NPV metrics for project evaluation.
"""

from re_storage.financial.debt import calculate_amortization_schedule, size_debt_for_dscr
from re_storage.financial.metrics import (
    calculate_dscr_series,
    calculate_equity_irr,
    calculate_npv,
    calculate_project_irr,
)
from re_storage.financial.waterfall import build_cash_flow_waterfall

__all__ = [
    "build_cash_flow_waterfall",
    "calculate_amortization_schedule",
    "size_debt_for_dscr",
    "calculate_npv",
    "calculate_project_irr",
    "calculate_equity_irr",
    "calculate_dscr_series",
]
