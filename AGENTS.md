# AGENTS.md — Rules of Engagement

> **Purpose:** This document governs all AI agents and human developers working on the RE-Storage Financial Model simulation engine. Treat this as the constitution of the codebase.

---

## 1. Project Philosophy

### 1.1 The Prime Directive

> **"Physics First, Finance Second."**

Every simulation must satisfy **mass balance (kWh)** before applying **tariffs ($)**. If energy doesn't balance, the money is meaningless.

**Validation Order:**
1. ✅ Energy in = Energy out + Losses (verify `Balance_Check == 0`)
2. ✅ SoC stays within `[0, Usable_BESS_Capacity]` at all timesteps
3. ✅ Power flows respect equipment ratings (inverter limits, grid connection)
4. 💰 *Only then* apply tariffs, prices, and financial calculations

### 1.2 Auditability Over Cleverness

This is a **financial model for project finance**. Every calculation must be:
- **Traceable:** An auditor should be able to follow any number back to its source
- **Reproducible:** Given the same inputs, outputs must be identical (no random seeds without explicit control)
- **Explainable:** Code comments explain the *financial/engineering rationale*, not just what the code does

### 1.3 Defensive Programming

Assume inputs will be wrong. The model should:
- **Fail loudly** on invalid inputs (don't silently produce garbage)
- **Warn explicitly** on edge cases (e.g., DPPA revenue = 0, Loss table incomplete)
- **Never mutate** input data — always work on copies

---

## 2. Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Language** | Python 3.11+ | Type hints, performance, ecosystem |
| **Core Computation** | `pandas` + `numpy` | Vectorized operations for 8760+ rows |
| **Configuration** | `pydantic` | Strict schema validation for inputs |
| **Testing** | `pytest` + `hypothesis` | Property-based testing for edge cases |
| **Documentation** | Sphinx + Google-style docstrings | Auto-generated API docs |
| **Type Checking** | `mypy --strict` | Catch errors before runtime |
| **Formatting** | `black` + `isort` + `ruff` | Consistent style, no debates |

### 2.1 Optional Extensions

| Use Case | Technology |
|----------|------------|
| Optimization (debt sizing) | `scipy.optimize` or `cvxpy` |
| Visualization | `plotly` or `matplotlib` |
| Excel I/O | `openpyxl` (read-only preferred) |
| CLI Interface | `typer` |
| Parallel Scenarios | `joblib` or `multiprocessing` |

---

## 3. Coding Standards

### 3.1 Type Hinting (Mandatory)

Every function signature must have complete type annotations.

```python
# ✅ CORRECT
def calculate_soc(
    previous_soc_kwh: float,
    charged_kwh: float,
    discharged_kwh: float,
    charge_efficiency: float,
    discharge_efficiency: float,
    max_capacity_kwh: float,
) -> float:
    """Calculate battery state of charge after a timestep."""
    ...

# ❌ WRONG - No type hints
def calculate_soc(previous_soc, charged, discharged, eff_c, eff_d, max_cap):
    ...
```

### 3.2 Immutability (Critical for Audit Trails)

**Rule:** Prefer "pass by value" semantics. Never mutate input DataFrames.

```python
# ✅ CORRECT - Return new DataFrame
def add_solar_generation(hourly_data: pd.DataFrame, scale_factor: float) -> pd.DataFrame:
    """Add scaled solar generation column. Does not mutate input."""
    result = hourly_data.copy()
    result["solar_gen_kw"] = result["simulation_profile_kw"] * scale_factor
    return result

# ❌ WRONG - Mutates input (side effect)
def add_solar_generation(hourly_data: pd.DataFrame, scale_factor: float) -> None:
    hourly_data["solar_gen_kw"] = hourly_data["simulation_profile_kw"] * scale_factor
```

**Why:** Financial models require audit trails. If an intermediate DataFrame is mutated, we lose the ability to trace how a number was derived.

### 3.3 Documentation Standards

Every function must have a docstring explaining:
1. **What** — Brief description
2. **Why** — Financial/engineering rationale (the "business logic")
3. **Args** — Each parameter with units
4. **Returns** — Output with units
5. **Raises** — Expected exceptions

```python
def calculate_cfd_settlement(
    consumed_re_kwh: float,
    strike_price_usd_per_kwh: float,
    spot_price_usd_per_kwh: float,
) -> float:
    """
    Calculate Contract-for-Difference (CfD) settlement payment.

    The CfD mechanism creates a synthetic fixed price for renewable energy:
    - If spot < strike: Seller receives top-up (positive revenue)
    - If spot > strike: Seller pays back difference (negative revenue)

    This hedges the generator against market price volatility while
    allowing participation in the wholesale market.

    Args:
        consumed_re_kwh: Renewable energy consumed by offtaker (kWh)
        strike_price_usd_per_kwh: Contracted fixed price ($/kWh)
        spot_price_usd_per_kwh: Market clearing price at delivery hour ($/kWh)

    Returns:
        CfD settlement amount in USD. Positive = payment to seller.

    Raises:
        ValueError: If consumed_re_kwh is negative.
    """
    if consumed_re_kwh < 0:
        raise ValueError(f"consumed_re_kwh cannot be negative: {consumed_re_kwh}")
    
    return consumed_re_kwh * (strike_price_usd_per_kwh - spot_price_usd_per_kwh)
```

### 3.4 Naming Conventions

| Entity | Convention | Example |
|--------|------------|---------|
| Variables | `snake_case` with units suffix | `solar_gen_kw`, `soc_kwh`, `price_usd_per_mwh` |
| Constants | `SCREAMING_SNAKE_CASE` | `HOURS_PER_YEAR = 8760` |
| Classes | `PascalCase` | `BatteryDispatcher`, `DPPACalculator` |
| Modules | `snake_case` | `battery_dispatch.py`, `dppa_settlement.py` |
| Type Aliases | `PascalCase` | `HourlyTimeSeries = pd.DataFrame` |

**Unit Suffixes (Mandatory for physical quantities):**
- `_kw` / `_mw` — Power
- `_kwh` / `_mwh` — Energy
- `_usd` / `_vnd` — Currency
- `_pct` — Percentage (0-100 scale)
- `_ratio` — Ratio (0-1 scale)

### 3.5 Error Handling

```python
# ✅ Use domain-specific exceptions
class EnergyBalanceError(Exception):
    """Raised when energy inputs don't equal outputs + losses."""
    pass

class InsufficientCapacityError(Exception):
    """Raised when requested power exceeds equipment rating."""
    pass

# ✅ Fail fast with context
def validate_soc(soc_kwh: float, max_capacity_kwh: float) -> None:
    if soc_kwh < 0:
        raise ValueError(f"SoC cannot be negative: {soc_kwh} kWh")
    if soc_kwh > max_capacity_kwh:
        raise ValueError(
            f"SoC ({soc_kwh} kWh) exceeds capacity ({max_capacity_kwh} kWh)"
        )
```

---

## 4. Testing Requirements

### 4.1 Test Categories

| Category | Purpose | Coverage Target |
|----------|---------|-----------------|
| **Unit Tests** | Individual functions | 100% of public API |
| **Integration Tests** | Module interactions | All data flows in architecture |
| **Property Tests** | Invariants (e.g., SoC bounds) | All physical constraints |
| **Regression Tests** | Match Excel model outputs | Key KPIs within tolerance |
| **Edge Case Tests** | Boundary conditions | All risks from §4 of architecture doc |

### 4.2 Property-Based Testing (Mandatory for Physics)

```python
from hypothesis import given, strategies as st

@given(
    soc=st.floats(min_value=0, max_value=100),
    charge=st.floats(min_value=0, max_value=50),
    discharge=st.floats(min_value=0, max_value=50),
)
def test_soc_always_bounded(soc: float, charge: float, discharge: float) -> None:
    """SoC must always remain within [0, max_capacity]."""
    result = calculate_soc(soc, charge, discharge, eff_c=0.9, eff_d=0.9, max_cap=100)
    assert 0 <= result <= 100, f"SoC out of bounds: {result}"
```

### 4.3 Regression Test Tolerance

When comparing Python outputs to Excel reference values:

| Metric | Acceptable Tolerance |
|--------|---------------------|
| Energy (kWh/MWh) | ±0.01% |
| Revenue/Cost ($) | ±0.01% |
| IRR (%) | ±0.0001 (absolute) |
| DSCR (ratio) | ±0.001 |

---

## 5. Git Workflow

### 5.1 Branch Naming

```
feature/battery-dispatch-logic
bugfix/soc-overflow-edge-case
refactor/dppa-module-split
docs/api-reference-update
```

### 5.2 Commit Messages

```
feat(battery): implement time-window arbitrage charging mode

- Add PV-to-BESS diversion based on ActivePV2BESS_Mode=1
- Respect Min_DirectPVShare constraint
- Includes unit tests for edge cases

Refs: model_architecture.md §A.2
```

### 5.3 Pull Request Checklist

- [ ] All tests pass (`pytest`)
- [ ] Type checks pass (`mypy --strict`)
- [ ] Linting passes (`ruff check`)
- [ ] Docstrings complete for new functions
- [ ] Energy balance validated (if physics changes)
- [ ] Regression tests updated (if output changes)

---

## 6. File Structure (Target)

```
RE-storage-model/
├── AGENTS.md                    # This file
├── implementation_spec.md       # Technical architecture
├── model_architecture.md        # Domain logic (reference)
├── pyproject.toml               # Project config & dependencies
├── src/
│   └── re_storage/
│       ├── __init__.py
│       ├── core/                # Domain models & types
│       │   ├── __init__.py
│       │   ├── types.py         # Type aliases, enums
│       │   └── exceptions.py    # Domain exceptions
│       ├── inputs/              # Input loading & validation
│       │   ├── __init__.py
│       │   ├── schemas.py       # Pydantic models
│       │   └── loaders.py       # Excel/CSV readers
│       ├── physics/             # Energy simulation
│       │   ├── __init__.py
│       │   ├── solar.py         # PV generation
│       │   ├── battery.py       # BESS dispatch
│       │   └── balance.py       # Energy balance validation
│       ├── settlement/          # Revenue calculations
│       │   ├── __init__.py
│       │   ├── dppa.py          # DPPA/CfD logic
│       │   └── grid.py          # Grid charges & savings
│       ├── aggregation/         # Time-scale bridging
│       │   ├── __init__.py
│       │   ├── monthly.py       # Hourly → Monthly
│       │   ├── annual.py        # Monthly → Annual
│       │   └── lifetime.py      # Annual → 25-year
│       ├── financial/           # Cash flow & returns
│       │   ├── __init__.py
│       │   ├── waterfall.py     # Revenue - Opex - Debt
│       │   ├── debt.py          # Debt sizing & DSCR
│       │   └── metrics.py       # IRR, NPV, DSCR
│       └── validation/          # Cross-cutting validation
│           ├── __init__.py
│           └── checks.py        # Balance checks, warnings
├── tests/
│   ├── conftest.py              # Fixtures
│   ├── unit/                    # Unit tests by module
│   ├── integration/             # Cross-module tests
│   ├── regression/              # Excel comparison tests
│   └── data/                    # Test fixtures (mini datasets)
└── notebooks/                   # Exploration & debugging
    └── model_comparison.ipynb
```

---

## 7. Anti-Patterns (What NOT to Do)

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Leave `# TODO` comments | Implement or create GitHub issue |
| Use `Any` type hint | Define proper types or protocols |
| Catch generic `Exception` | Catch specific exceptions |
| Use magic numbers | Define named constants with units |
| Mutate function arguments | Return new objects |
| Skip docstrings "for now" | Write docstring before implementation |
| Hardcode file paths | Use configuration or parameters |
| Print debug output | Use `logging` module |
| Assume Excel formulas are correct | Validate against first principles |

---

## 8. Communication Protocol

When an AI agent is uncertain:

1. **State the uncertainty explicitly** — "I am unsure whether the discharge efficiency applies before or after the inverter."
2. **Reference the source** — "model_architecture.md §A.4 says X, but I interpret it as Y."
3. **Propose options** — "Option A: [approach]. Option B: [approach]. Recommend A because [reason]."
4. **Ask for clarification** — Don't guess on financial logic.

---

*Document Version: 1.0*  
*Created: 2026-01-29*  
*Last Updated: 2026-01-29*
