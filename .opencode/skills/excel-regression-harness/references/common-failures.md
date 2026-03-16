# Common Failures

## Extracted KPI is None

Cause:

- `openpyxl` reads cached formula values; workbook cache can be stale.

Recovery:

1. Open workbook in Excel.
2. Press `Ctrl+Shift+F9` to recalculate.
3. Save workbook.
4. Re-run extraction script.

## Regression Mismatch After Fixture Update

Checklist:

1. Confirm reference JSON was regenerated.
2. Confirm correct workbook/reference filename pairing.
3. Run `test_physics_layer` to isolate simulation issues.
4. Run `test_financial_kpis` to isolate waterfall/debt/metrics issues.

## Missing Auto-Discovery Pair

Cause:

- Workbook exists without same-stem JSON, or vice versa.

Recovery:

- Regenerate references and verify stems match exactly.
