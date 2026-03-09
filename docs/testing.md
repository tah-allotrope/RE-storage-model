# Testing

## Test Categories

| Category | Purpose |
|----------|---------|
| **Unit Tests** | Individual functions |
| **Integration Tests** | Module interactions |
| **Property Tests** | Invariants (e.g., SoC bounds) |
| **Regression Tests** | Match Excel model outputs |
| **Edge Case Tests** | Boundary conditions |

## Property-Based Testing (Mandatory for Physics)

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

## Regression Test Tolerance

| Metric | Acceptable Tolerance |
|--------|---------------------|
| Energy (kWh/MWh) | ±0.01% |
| Revenue/Cost ($) | ±0.01% |
| IRR (%) | ±0.0001 (absolute) |
| DSCR (ratio) | ±0.001 |
