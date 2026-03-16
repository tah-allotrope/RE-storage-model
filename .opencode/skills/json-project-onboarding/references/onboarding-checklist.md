# Onboarding Checklist

1. Confirm project directory contains exactly one `.json` and one `.csv`.
2. Map JSON fields to `SystemAssumptions`.
3. Normalize CSV columns to internal schema names.
4. Validate hourly row count and required columns.
5. Build degradation table for declared project lifetime.
6. Build tariff rates mapping and unit conversions.
7. Parse financial parameters (rate, tenor, DSCR, capex, dates).
8. Ensure `run_model_from_json()` uses internal pipeline stages directly.
9. Return `_hourly_df` and `_lifetime_df` alongside scalar KPIs.
10. Add/refresh unit + regression tests.
