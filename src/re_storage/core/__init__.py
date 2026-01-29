"""
Core module: Domain types, constants, and exceptions.

This module provides the foundational building blocks used across
the entire RE-Storage simulation engine.
"""

from re_storage.core.exceptions import (
    DSCRConstraintError,
    DegradationTableError,
    EnergyBalanceError,
    InputValidationError,
    InsufficientCapacityError,
    REStorageError,
    SoCBoundsError,
)
from re_storage.core.types import (
    ChargingMode,
    EnergyKWH,
    EnergyMWH,
    HourlyTimeSeries,
    MonthlyTimeSeries,
    AnnualTimeSeries,
    Percentage,
    PowerKW,
    PriceUSDPerKWH,
    Ratio,
    StrategyMode,
    TimePeriod,
    HOURS_PER_YEAR,
    HOURS_PER_LEAP_YEAR,
)

__all__ = [
    # Exceptions
    "REStorageError",
    "EnergyBalanceError",
    "SoCBoundsError",
    "InsufficientCapacityError",
    "InputValidationError",
    "DegradationTableError",
    "DSCRConstraintError",
    # Types
    "HourlyTimeSeries",
    "MonthlyTimeSeries",
    "AnnualTimeSeries",
    "PowerKW",
    "EnergyKWH",
    "EnergyMWH",
    "PriceUSDPerKWH",
    "Ratio",
    "Percentage",
    # Enums
    "StrategyMode",
    "ChargingMode",
    "TimePeriod",
    # Constants
    "HOURS_PER_YEAR",
    "HOURS_PER_LEAP_YEAR",
]
