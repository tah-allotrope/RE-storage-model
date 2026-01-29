"""
Aggregation layer for time-scale bridging.

This package converts hourly simulation outputs into monthly and annual
summaries, then projects results across the project lifetime.
"""

from re_storage.aggregation.annual import (
    calculate_total_dppa_revenue_usd,
    calculate_total_solar_generation_mwh,
    calculate_year1_totals,
)
from re_storage.aggregation.lifetime import (
    build_lifetime_projection,
    project_battery_capacity_kwh,
    project_lifetime_generation_mwh,
)
from re_storage.aggregation.monthly import aggregate_hourly_to_monthly

__all__ = [
    "aggregate_hourly_to_monthly",
    "calculate_total_dppa_revenue_usd",
    "calculate_total_solar_generation_mwh",
    "calculate_year1_totals",
    "project_lifetime_generation_mwh",
    "project_battery_capacity_kwh",
    "build_lifetime_projection",
]
