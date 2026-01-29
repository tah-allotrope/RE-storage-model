"""
Settlement module: DPPA/CfD revenue and grid expense calculations.

This package converts physics outputs into hourly financial settlement values.
"""

from re_storage.settlement.dppa import (
    calculate_cfd_settlement,
    calculate_consumed_re,
    calculate_delivered_re,
    calculate_dppa_revenue,
    calculate_market_revenue,
    calculate_total_dppa_revenue,
)
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_demand_charges,
    calculate_energy_expense,
    calculate_grid_savings,
    calculate_re_expense,
)

__all__ = [
    "calculate_delivered_re",
    "calculate_consumed_re",
    "calculate_market_revenue",
    "calculate_cfd_settlement",
    "calculate_total_dppa_revenue",
    "calculate_dppa_revenue",
    "calculate_energy_expense",
    "calculate_bau_expense",
    "calculate_re_expense",
    "calculate_demand_charges",
    "calculate_grid_savings",
]
