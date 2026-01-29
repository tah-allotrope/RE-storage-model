"""
Domain-specific type aliases and enumerations.

This module defines type aliases for documentation and IDE support,
as well as enumerations for categorical values used throughout the model.

Note: Type aliases in Python do not provide runtime enforcement.
They serve as documentation and enable static type checking with mypy.

Naming Convention (from AGENTS.md):
    - Variables: snake_case with unit suffix (_kw, _kwh, _usd, _pct, _ratio)
    - Constants: SCREAMING_SNAKE_CASE
    - Type Aliases: PascalCase
    - Enums: PascalCase with SCREAMING_SNAKE_CASE members
"""

from enum import Enum, auto
from typing import TypeAlias

import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================

HOURS_PER_YEAR: int = 8760
"""Standard hours in a non-leap year."""

HOURS_PER_LEAP_YEAR: int = 8784
"""Hours in a leap year (366 days × 24 hours)."""

DEFAULT_STEP_HOURS: float = 1.0
"""Default simulation timestep in hours."""


# =============================================================================
# TIME SERIES TYPE ALIASES
# =============================================================================

HourlyTimeSeries: TypeAlias = pd.DataFrame
"""
DataFrame representing hourly time series data.

Expected structure:
    - Index: datetime or integer (0 to 8759/8783)
    - Rows: 8760 (standard year) or 8784 (leap year)
    - Columns: Depend on context (e.g., solar_gen_kw, load_kw, soc_kwh)
"""

MonthlyTimeSeries: TypeAlias = pd.DataFrame
"""
DataFrame representing monthly aggregated data.

Expected structure:
    - Index: month (1-12) or datetime (first of month)
    - Rows: 12
    - Columns: Aggregated metrics (e.g., peak_demand_kw, total_revenue_usd)
"""

AnnualTimeSeries: TypeAlias = pd.DataFrame
"""
DataFrame representing annual data over project lifetime.

Expected structure:
    - Index: year (1-25) or calendar year
    - Rows: Typically 25 (project lifetime)
    - Columns: Annual metrics (e.g., generation_mwh, revenue_usd, dscr)
"""


# =============================================================================
# PHYSICAL UNIT TYPE ALIASES
# =============================================================================
# These aliases document expected units. They do NOT enforce units at runtime.
# Use them for function signatures and variable declarations.

PowerKW: TypeAlias = float
"""Power in kilowatts (kW). Instantaneous rate of energy flow."""

EnergyKWH: TypeAlias = float
"""Energy in kilowatt-hours (kWh). Power integrated over time."""

EnergyMWH: TypeAlias = float
"""Energy in megawatt-hours (MWh). 1 MWh = 1000 kWh."""

PriceUSDPerKWH: TypeAlias = float
"""Price in US dollars per kilowatt-hour ($/kWh)."""

Ratio: TypeAlias = float
"""
Dimensionless ratio on 0.0 to 1.0 scale.

Examples: efficiency (0.85), capacity factor (0.22), loss factor (0.02)
"""

Percentage: TypeAlias = float
"""
Percentage on 0.0 to 100.0 scale.

Examples: degradation rate (0.5%), IRR (8.83%)
Note: Always clarify in docstrings whether 5% is 5.0 or 0.05.
"""


# =============================================================================
# ENUMERATIONS
# =============================================================================

class StrategyMode(Enum):
    """
    Battery dispatch strategy mode.

    Determines the high-level objective of battery operation:
    - ARBITRAGE: Maximize time-of-use arbitrage (buy low, sell high)
    - PEAK_SHAVING: Minimize demand charges by reducing peak grid load

    Reference: model_architecture.md §A.3 (Strategy_mode)
    """

    ARBITRAGE = 1
    PEAK_SHAVING = 2


class ChargingMode(Enum):
    """
    PV-to-BESS charging strategy.

    Determines how/when solar energy is diverted to charge the battery:
    - TIME_WINDOW: Charge during specific hours (e.g., 9am-3pm)
    - PRECHARGE_TARGET: Charge to reach target SoC by a specific hour

    Reference: model_architecture.md §A.2 (ActivePV2BESS_Mode)
    """

    TIME_WINDOW = 1
    PRECHARGE_TARGET = 2


class TimePeriod(Enum):
    """
    Electricity tariff period classification.

    Used to determine applicable electricity rates:
    - OFF_PEAK: Lowest rates (typically night hours)
    - STANDARD: Mid-tier rates (daytime, non-peak)
    - PEAK: Highest rates (typically 17:00-20:00)

    Reference: Vietnam EVN tariff structure
    """

    OFF_PEAK = auto()
    STANDARD = auto()
    PEAK = auto()


class GridChargeMode(Enum):
    """
    Grid-to-BESS charging mode.

    Determines if and how the battery can charge from the grid:
    - DISABLED: No grid charging allowed
    - TO_TARGET: Charge to CapGrid target capacity
    - TO_FULL: Charge to full usable capacity

    Reference: model_architecture.md Risk 2 (GridChargeAllowFlag)
    """

    DISABLED = 0
    TO_TARGET = 1
    TO_FULL = 2
