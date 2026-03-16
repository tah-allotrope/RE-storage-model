# Tolerance Tiers

Follow project tolerance tiers used by regression tests:

- Energy (kWh/MWh): relative `0.0001` (±0.01%)
- Revenue/Cost (USD): relative `0.0001` (±0.01%)
- IRR: absolute `0.0001`
- DSCR: absolute `0.001`
- NPV: relative `0.0001` (±0.01%)

Comparison modes:

- `abs`: compare `abs(actual - expected) <= tolerance`
- `rel`: compare `abs(actual - expected) / abs(expected) <= tolerance`

When expected is approximately zero, use absolute fallback logic.
