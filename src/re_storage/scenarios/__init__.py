"""
Scenario analysis: multi-scenario comparison and sensitivity sweeps.
"""

from re_storage.scenarios.runner import run_all_scenarios
from re_storage.scenarios.sensitivity import (
    SENSITIVITY_VARIABLES,
    STANDARD_VARIABLE_NAMES,
    SensitivityPoint,
    build_sensitivity_dataframe,
    plot_tornado_chart,
    run_full_sensitivity,
    run_sensitivity,
    run_sensitivity_for_values,
)

__all__ = [
    "run_all_scenarios",
    # New high-level sensitivity API
    "run_sensitivity",
    "run_full_sensitivity",
    "build_sensitivity_dataframe",
    "plot_tornado_chart",
    # Result type
    "SensitivityPoint",
    # Variable registry
    "SENSITIVITY_VARIABLES",
    "STANDARD_VARIABLE_NAMES",
    # Backward-compatible lower-level API
    "run_sensitivity_for_values",
]
