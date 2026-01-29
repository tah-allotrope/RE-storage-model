"""
RE-Storage: Vietnam Solar + BESS Financial Model Simulation Engine.

This package implements a Python simulation engine for modeling solar PV
and battery energy storage systems (BESS) for project finance applications.

Philosophy: "Physics First, Finance Second"
- Energy balance (kWh) must be validated before applying tariffs ($)
- All calculations are auditable and reproducible

Modules:
    core: Domain types and exceptions
    physics: Energy simulation (solar generation, battery dispatch)
    settlement: Revenue calculations (DPPA, grid savings)
    aggregation: Time-scale bridging (hourly → annual → lifetime)
    financial: Cash flow and return metrics
    validation: Cross-cutting validation checks
"""

__version__ = "0.1.0"
