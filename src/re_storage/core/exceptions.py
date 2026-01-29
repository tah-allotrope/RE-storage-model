"""
Domain-specific exceptions for the RE-Storage simulation engine.

This module defines a hierarchy of exceptions that provide clear,
actionable error messages for common failure modes in the model.

Exception Hierarchy:
    REStorageError (base)
    ├── EnergyBalanceError     - Physics validation failed
    ├── SoCBoundsError         - Battery SoC out of bounds
    ├── InsufficientCapacityError - Power exceeds equipment rating
    ├── InputValidationError   - Input data failed validation
    ├── DegradationTableError  - Loss table incomplete/malformed
    └── DSCRConstraintError    - Debt sizing infeasible

Design Principle (from AGENTS.md):
    "Fail loudly on invalid inputs (don't silently produce garbage)"
"""


class REStorageError(Exception):
    """
    Base exception for all RE-Storage model errors.

    All domain-specific exceptions inherit from this class, allowing
    callers to catch all model errors with a single except clause
    while still being able to catch specific error types.

    Example:
        try:
            run_simulation(data)
        except REStorageError as e:
            logger.error(f"Simulation failed: {e}")
    """

    pass


class EnergyBalanceError(REStorageError):
    """
    Energy inputs do not equal outputs plus losses.

    This exception enforces the "Physics First" principle: every
    kilowatt-hour must be accounted for before applying financial
    calculations.

    Validation Formula:
        Solar_Gen = Direct_Consumption + Charged + Surplus (± tolerance)

    Typical Causes:
        - Bug in dispatch logic creating/destroying energy
        - Incorrect efficiency factors
        - Timestep alignment issues

    Args:
        message: Description of the imbalance
        imbalance_kwh: The energy discrepancy (optional)
        timestep: The timestep where imbalance occurred (optional)
    """

    def __init__(
        self,
        message: str,
        imbalance_kwh: float | None = None,
        timestep: int | None = None,
    ) -> None:
        self.imbalance_kwh = imbalance_kwh
        self.timestep = timestep
        super().__init__(message)


class SoCBoundsError(REStorageError):
    """
    Battery State of Charge exceeded valid bounds [0, max_capacity].

    The battery cannot have negative energy (over-discharged) or
    more energy than its physical capacity (over-charged).

    Typical Causes:
        - Dispatch logic allowed discharge when SoC was zero
        - Charge limit calculation error
        - Incorrect efficiency application

    Args:
        message: Description of the violation
        soc_kwh: The invalid SoC value
        max_capacity_kwh: The maximum allowed capacity
        timestep: The timestep where violation occurred (optional)
    """

    def __init__(
        self,
        message: str,
        soc_kwh: float | None = None,
        max_capacity_kwh: float | None = None,
        timestep: int | None = None,
    ) -> None:
        self.soc_kwh = soc_kwh
        self.max_capacity_kwh = max_capacity_kwh
        self.timestep = timestep
        super().__init__(message)


class InsufficientCapacityError(REStorageError):
    """
    Requested power exceeds equipment rating.

    Power flows are constrained by physical equipment limits:
    - Battery inverter rating (kW)
    - Grid connection capacity (kW)
    - Transformer rating (kVA)

    Typical Causes:
        - Load exceeds grid connection limit
        - Discharge request exceeds inverter rating
        - Configuration error in capacity parameters

    Args:
        message: Description of the violation
        requested_kw: Power that was requested
        available_kw: Maximum available power
    """

    def __init__(
        self,
        message: str,
        requested_kw: float | None = None,
        available_kw: float | None = None,
    ) -> None:
        self.requested_kw = requested_kw
        self.available_kw = available_kw
        super().__init__(message)


class InputValidationError(REStorageError):
    """
    Input data failed schema validation.

    Raised when input data (from Excel, CSV, or API) does not
    conform to expected schemas defined in inputs.schemas.

    Typical Causes:
        - Missing required columns in time series data
        - Invalid values (negative capacity, efficiency > 1.0)
        - Wrong number of rows (not 8760/8784 for hourly data)
        - Type mismatches

    Args:
        message: Description of validation failure
        field: The specific field that failed validation (optional)
        value: The invalid value (optional)
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: object | None = None,
    ) -> None:
        self.field = field
        self.value = value
        super().__init__(message)


class DegradationTableError(REStorageError):
    """
    Loss/degradation table is incomplete or malformed.

    The degradation table must cover all project years (typically 1-25)
    for both PV and battery degradation factors.

    Reference: model_architecture.md Risk 5 (Loss table year alignment)

    Typical Causes:
        - Table only covers years 1-20 but project is 25 years
        - Missing columns (pv_factor, battery_factor)
        - Invalid factor values (>1.0 or <0)

    Args:
        message: Description of the issue
        missing_years: List of years not covered (optional)
    """

    def __init__(
        self,
        message: str,
        missing_years: list[int] | None = None,
    ) -> None:
        self.missing_years = missing_years
        super().__init__(message)


class DSCRConstraintError(REStorageError):
    """
    Debt sizing failed to satisfy DSCR covenant.

    The Debt Service Coverage Ratio (DSCR) must meet a minimum
    threshold (typically 1.2x-1.4x) in all years. If no debt amount
    can satisfy this constraint, the project is not bankable.

    Reference: model_architecture.md §D.3 (Debt Service)

    Typical Causes:
        - EBITDA too low relative to required debt service
        - Interest rate too high
        - Debt tenor too short
        - Revenue projections insufficient

    Args:
        message: Description of the constraint violation
        min_dscr_achieved: The lowest DSCR found during optimization
        target_dscr: The required minimum DSCR
    """

    def __init__(
        self,
        message: str,
        min_dscr_achieved: float | None = None,
        target_dscr: float | None = None,
    ) -> None:
        self.min_dscr_achieved = min_dscr_achieved
        self.target_dscr = target_dscr
        super().__init__(message)
