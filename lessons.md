# Lessons Learned

Project-specific rules that should prevent recurrence of mistakes or
re-derivation of patterns. Reviewed at session start.

## Communication

### L-001 — "Grill me" = surface existing questions, not generate new ones
**Pattern:** When a plan contains a `## Grill Me` section, "grill me on this plan"
from the user means **list the questions the plan author already asked**, not
"invent fresh stress-test questions."
**Rule:** If the file has a `Grill Me` heading, read that section first and
report its contents verbatim. Only generate new probing questions if the user
explicitly asks "ask me questions about" or "stress-test the plan."
**Cost of getting it wrong:** Wastes a turn re-grounding in the repo to invent
questions the user could have read themselves.

## Web Handler Patterns

### L-002 — Cloud Function exports re-run the model; do not cache DataFrames
**Pattern:** `_hourly_df`, `_lifetime_df`, `_annual_df` are large and discarded
after JSON serialisation. Trying to cache them across requests couples the
feature to Firestore/Storage (GAP-04) and adds an entire layer of state.
**Rule:** Stateless Cloud Function exports (HTML report, xlsx workbook) should
re-run `run_model_from_json` / `run_full_model` from the posted inputs. The
model runs in ~2–10 s; that latency is the price of zero infrastructure
coupling. Revisit only if profiling shows the re-run dominates response time.
**Reference:** `web/functions/handlers/run_report.py`,
`web/functions/handlers/export_workbook.py`.

### L-003 — Dual-source handler pattern via `source` form field
**Pattern:** Web users come from two paths — structured form + hourly CSV
(JSON model) or `.xlsx` upload (Excel model). Two endpoints per feature is
wasteful; one endpoint with a `source=json|excel` form-field switch keeps the
frontend simple and the URL surface small.
**Rule:** New export/result endpoints should accept `source` (default `json`)
and branch internally to `_handle_json_source` / `_handle_excel_source`,
mirroring `run_json.py` / `run_excel.py` for validation + temp-file handling.
**Reference:** `web/functions/handlers/run_report.py:115`.

### L-004 — Frontend needs CORS `Content-Disposition` exposed to read filenames
**Pattern:** `Access-Control-Expose-Headers: Content-Disposition` must be set
**both** on the Flask response and via `@cross_origin(expose_headers=...)` on
the Cloud Function entrypoint. Without it, the browser hides the header from
`fetch().headers.get("Content-Disposition")` even though it's in the wire
response.
**Rule:** Any handler that returns a downloadable artifact must:
1. Set `"Access-Control-Expose-Headers": "Content-Disposition"` in the
   `Response` headers.
2. Decorate the entrypoint in `main.py` with
   `@cross_origin(expose_headers=["Content-Disposition"])`.
3. Frontend `api/client.ts` should still fall back to a sensible filename
   when parsing fails (dev-proxy / older browsers).
**Reference:** `web/functions/main.py::runReport` /
`web/frontend/src/api/client.ts::parseContentDispositionFilename`.

### L-005 — Excel response tests should unzip via `openpyxl.load_workbook(BytesIO)`
**Pattern:** Asserting `body[:2] == b"PK"` only confirms the response is *some*
zip; it doesn't catch a 0-sheet workbook or wrong content.
**Rule:** xlsx download tests must (a) check zip magic bytes for fast failure
and (b) `openpyxl.load_workbook(io.BytesIO(body))` and assert expected
`sheetnames` are present and unexpected ones are absent (scope guard).
**Reference:** `tests/unit/test_web_handlers.py::test_handle_export_workbook_json_path_returns_xlsx`.

## Type Checking

### L-006 — Pre-existing `tuple[Response, int]` mypy errors in web handlers
**Pattern:** Existing handlers return `jsonify(...), 400` tuples but their
return type is annotated `Response`. Mypy `--strict` flags this as
`Incompatible return value type`. This is systemic across `run_excel.py`,
`run_json.py`, etc. — not a regression introduced by new handlers.
**Rule:** When adding a new web handler, follow the existing pattern (return
`tuple[Response, int]` for non-200 paths via `jsonify(...), STATUS`). Do not
attempt to "fix" mypy by changing the type to `Response | tuple[Response, int]`
piecemeal — either fix all handlers at once in a typed-cleanup PR or accept
the pre-existing systemic warning.
**Reference:** `web/functions/handlers/run_excel.py:20-44`,
`web/functions/handlers/run_report.py`.

### L-007 — JSON loader does NOT auto-read `tariff_structure` from the payload
**Pattern:** When wiring `tariff_mode` into the web tool (GAP-03), it was
tempting to assume `run_model_from_json(project_dir)` would pick the mode up
from the project JSON's `grid_connection_and_tariff.tariff_structure` field —
since the Excel loader does exactly that (parses a "Tariff Structure" cell
into `tariff_mode`). It does not. The JSON pipeline path requires the
`tariff_mode` kwarg to be passed explicitly; the payload field is documentation
only on the JSON path.
**Rule:** When threading a new pipeline kwarg through a web handler, pass it
**explicitly** as a kwarg to `run_model_from_json` / `run_full_model` even if
the same value lives in the JSON payload. The JSON loader is not symmetric
with the Excel loader on every field. Verify in the pipeline source before
relying on payload-side wiring.
**Reference:** `web/functions/handlers/run_json.py::handle_run_json`,
`src/re_storage/pipeline.py::run_model_from_json` (signature: `tariff_mode: str = "1-component"`).

### L-008 — Test fakes need `**kwargs` when handler signatures grow
**Pattern:** Adding a new kwarg to a pipeline call (e.g. `tariff_mode`,
`cp_demand_vnd_per_kw`) in a handler broke 8 pre-existing tests in
`test_web_handlers.py` because their `monkeypatch.setattr(..., fake_fn)` fakes
were narrowly typed (`def fake_run_full_model(_: Path) -> dict[str, float]`)
and rejected the new kwargs with `TypeError`, which surfaced as a 500 from
the catch-all `except Exception`. The real bug was in the test, not the
handler, but the 500 hid that.
**Rule:** Mock fakes for pipeline entrypoints (`run_full_model`,
`run_model_from_json`, `run_all_scenarios`, `run_sensitivity_for_values`,
`run_tariff_mode_comparison`) should accept `**_kwargs: Any` from day one.
Sketch:
```python
def fake_run_full_model(_: Path, **_kwargs: Any) -> dict[str, float]:
    ...
```
**Reference:** `tests/unit/test_web_handlers.py::test_handle_run_excel_success`
and 7 other fakes updated in commit `bcb52e4`.
