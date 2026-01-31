# Regression Test Fixtures

Place the Excel reference file at `tests/data/excel_reference.xlsx` when available.

The regression test expects a model entrypoint named `run_full_model` in
`re_storage.pipeline` that accepts the Excel path and returns metrics as:

- a dict with keys `project_irr`, `equity_irr`, `unlevered_irr`, `npv_usd`, or
- an object exposing those metrics as attributes, or
- an object with a `.metrics` dict containing those keys.
