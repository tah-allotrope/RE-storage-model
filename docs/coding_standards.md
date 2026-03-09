# Coding Standards

## Type Hinting (Mandatory)

Every function signature must have complete type annotations.

```python
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
```

## Immutability (Critical for Audit Trails)

Prefer "pass by value" semantics. Never mutate input DataFrames.

```python
def add_solar_generation(hourly_data: pd.DataFrame, scale_factor: float) -> pd.DataFrame:
    """Add scaled solar generation column. Does not mutate input."""
    result = hourly_data.copy()
    result["solar_gen_kw"] = result["simulation_profile_kw"] * scale_factor
    return result
```

## Documentation Standards

Every function must have a docstring explaining:
1. What — Brief description
2. Why — Financial/engineering rationale
3. Args — Each parameter with units
4. Returns — Output with units
5. Raises — Expected exceptions

```python
def calculate_cfd_settlement(
    consumed_re_kwh: float,
    strike_price_usd_per_kwh: float,
    spot_price_usd_per_kwh: float,
) -> float:
    """
    Calculate Contract-for-Difference (CfD) settlement payment.

    The CfD mechanism creates a synthetic fixed price for renewable energy.

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

## Naming Conventions

| Entity | Convention | Example |
|--------|------------|---------|
| Variables | `snake_case` with units suffix | `solar_gen_kw`, `soc_kwh` |
| Constants | `SCREAMING_SNAKE_CASE` | `HOURS_PER_YEAR = 8760` |
| Classes | `PascalCase` | `BatteryDispatcher` |
| Modules | `snake_case` | `battery_dispatch.py` |

**Unit Suffixes (Mandatory):**
- `_kw` / `_mw` — Power
- `_kwh` / `_mwh` — Energy
- `_usd` — Currency
- `_pct` — Percentage (0-100)
- `_ratio` — Ratio (0-1)

## Error Handling

```python
class EnergyBalanceError(Exception):
    """Raised when energy inputs don't equal outputs + losses."""
    pass

def validate_soc(soc_kwh: float, max_capacity_kwh: float) -> None:
    if soc_kwh < 0:
        raise ValueError(f"SoC cannot be negative: {soc_kwh} kWh")
    if soc_kwh > max_capacity_kwh:
        raise ValueError(f"SoC ({soc_kwh} kWh) exceeds capacity ({max_capacity_kwh} kWh)")
```

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Leave `# TODO` comments | Implement or create GitHub issue |
| Use `Any` type hint | Define proper types |
| Catch generic `Exception` | Catch specific exceptions |
| Use magic numbers | Define named constants |
| Mutate function arguments | Return new objects |
| Hardcode file paths | Use configuration |
