"""
Validation module: cross-cutting checks and warnings.

This package aggregates physics, settlement, and financial validations into
helper functions that return warnings for auditability.
"""

from re_storage.validation.checks import (
    validate_augmentation_funding,
    validate_degradation_coverage,
    validate_dppa_revenue,
    validate_energy_balance_series,
    validate_full_model,
    validate_soc_bounds_series,
)

__all__ = [
    "validate_energy_balance_series",
    "validate_soc_bounds_series",
    "validate_dppa_revenue",
    "validate_degradation_coverage",
    "validate_augmentation_funding",
    "validate_full_model",
]
