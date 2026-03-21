"""
Settlement module: PPA revenue and grid expense calculations.

This package converts physics outputs into hourly financial settlement values
for all 4 supported PPA structures (Options 1–4).

The recommended entry-point for new code is the ``calculate_revenue``
dispatcher in ``settlement.revenue``, which accepts a ``PpaMode`` enum
and routes to the correct sub-module automatically.
"""

from re_storage.settlement.bundled import calculate_bundled_revenue
from re_storage.settlement.demand_charge import calculate_annual_demand_savings
from re_storage.settlement.dppa import (
    calculate_cfd_settlement,
    calculate_consumed_re,
    calculate_delivered_re,
    calculate_dppa_revenue,
    calculate_market_revenue,
    calculate_total_dppa_revenue,
)
from re_storage.settlement.fixed_ppa import calculate_fixed_ppa_revenue
from re_storage.settlement.grid import (
    calculate_bau_expense,
    calculate_demand_charges,
    calculate_energy_expense,
    calculate_grid_savings,
    calculate_re_expense,
)
from re_storage.settlement.revenue import PpaMode, calculate_revenue
from re_storage.settlement.separate import calculate_separate_revenue

__all__ = [
    # Dispatcher / enum (preferred API)
    "PpaMode",
    "calculate_revenue",
    # Individual settlement modules
    "calculate_annual_demand_savings",
    "calculate_bau_expense",
    "calculate_bundled_revenue",
    "calculate_cfd_settlement",
    "calculate_consumed_re",
    "calculate_delivered_re",
    "calculate_demand_charges",
    "calculate_dppa_revenue",
    "calculate_energy_expense",
    "calculate_fixed_ppa_revenue",
    "calculate_grid_savings",
    "calculate_market_revenue",
    "calculate_re_expense",
    "calculate_separate_revenue",
    "calculate_total_dppa_revenue",
]
