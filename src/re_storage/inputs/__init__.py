"""
Inputs module: Pydantic schemas and Excel/CSV loaders.

This package validates raw input data before it enters the physics engine.
"""

from re_storage.inputs.loaders import (
    load_assumptions,
    load_degradation_table,
    load_hourly_data,
    load_tariff_schedule,
)
from re_storage.inputs.schemas import DegradationRow, HourlyInputRow, SystemAssumptions

__all__ = [
    "SystemAssumptions",
    "HourlyInputRow",
    "DegradationRow",
    "load_assumptions",
    "load_hourly_data",
    "load_degradation_table",
    "load_tariff_schedule",
]
