# Test Patterns

Unit tests:

- Validate schema mapping and derived values.
- Validate CSV normalization and row count.
- Validate degradation table completeness for project years.
- Validate tariff and financial parameter conversions.

Regression tests:

- Smoke test model run.
- KPI key presence check.
- Physics sanity checks (solar generation range, SoC bounds).
- Full KPI comparison against reference file with skip behavior for null placeholders.

Suggested commands:

```bash
pytest tests/unit/test_json_loader.py -v
pytest tests/regression/test_emivest.py -v
pytest -v
```
