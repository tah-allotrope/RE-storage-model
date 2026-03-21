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
from re_storage.financial.mra import build_mra_schedule
from re_storage.financial.opex import build_opex_schedule
from re_storage.financial.taxes import (
    build_combined_depreciation_schedule,
    build_tax_rate_schedule,
    calculate_depreciation_schedule,
    calculate_levered_taxes,
    calculate_unlevered_taxes,
)
from re_storage.financial.waterfall import build_cash_flow_waterfall

__all__ = [
    "build_cash_flow_waterfall",
    "build_combined_depreciation_schedule",
    "build_mra_schedule",
    "build_opex_schedule",
    "build_tax_rate_schedule",
    "calculate_amortization_schedule",
    "calculate_depreciation_schedule",
    "calculate_dscr_series",
    "calculate_equity_irr",
    "calculate_levered_taxes",
    "calculate_npv",
    "calculate_project_irr",
    "calculate_unlevered_taxes",
    "size_debt_for_dscr",
]
