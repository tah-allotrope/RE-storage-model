# Implementation Plan — Inputs Layer (Schemas + Loaders)

## Why this design
We will keep **Pydantic models** in `inputs.schemas` for strict validation of scalar inputs and single-row structures, while `inputs.loaders` performs **DataFrame-level validation** for performance on 8760+ rows. This matches the "fail loudly" rule in **AGENTS.md** while avoiding expensive row-by-row validation for large time series.

---

## Step 1 — Create Inputs Package
**Files:**
- `src/re_storage/inputs/__init__.py`

**Purpose:**
Expose schema classes and loader functions for import stability.

---

## Step 2 — Implement `inputs.schemas`
**File:** `src/re_storage/inputs/schemas.py`

### Classes & Signatures
```python
class SystemAssumptions(BaseModel):
    simulation_capacity_kwp: float
    actual_capacity_kwp: float
    usable_bess_capacity_kwh: float
    bess_power_rating_kw: float
    charge_efficiency: float
    discharge_efficiency: float
    strategy_mode: int
    charging_mode: int
    charge_start_hour: int
    charge_end_hour: int
    precharge_target_hour: int
    precharge_target_soc_kwh: float
    min_direct_pv_share: float
    active_pv2bess_share: float
    demand_reduction_target: float
    strike_price_usd_per_kwh: float
    k_factor: float
    kpp: float
    bess_enabled: bool
    dppa_enabled: bool

    @property
    def scale_factor(self) -> float: ...
```

```python
class HourlyInputRow(BaseModel):
    datetime: datetime
    simulation_profile_kw: float
    irradiation_wh_m2: float
    load_kw: float
    fmp_usd_per_kwh: float
    cfmp_usd_per_kwh: float
```

```python
class DegradationRow(BaseModel):
    year: int
    pv_factor: float
    battery_factor_no_replacement: float
    battery_factor_with_replacement: float
```

### Validation Rules
- Use `Field` bounds from `implementation_spec.md`.
- `ConfigDict(extra="forbid")` to fail loudly on unexpected fields.
- `scale_factor` property computed from capacity ratio.

---

## Step 3 — Implement `inputs.loaders`
**File:** `src/re_storage/inputs/loaders.py`

### Functions & Signatures
```python
def load_assumptions(path: Path) -> SystemAssumptions: ...
```
- Reads `Assumptions` sheet with **one row** whose columns match `SystemAssumptions` fields.
- Raises `InputValidationError` if row count != 1 or missing fields.

```python
def load_hourly_data(path: Path) -> HourlyTimeSeries: ...
```
- Reads `Data Input` sheet.
- Validates required columns and row count ∈ {8760, 8784}.
- Validates non-negative columns (`simulation_profile_kw`, `irradiation_wh_m2`, `load_kw`).
- Raises `InputValidationError` on violations.

```python
def load_degradation_table(path: Path, project_years: int = 25) -> pd.DataFrame: ...
```
- Reads `Loss` sheet.
- Validates required columns and factor bounds.
- Validates coverage of years 1..project_years.
- Raises `InputValidationError` for malformed rows, `DegradationTableError` for missing years.

```python
def load_tariff_schedule(path: Path) -> dict[TimePeriod, list[int]]: ...
```
- Reads `Tariff Schedule` sheet with `hour` and `period` columns.
- Validates hour ∈ [0, 23] and period in {off_peak, standard, peak}.
- Returns a dict keyed by `TimePeriod` enums.

---

## Step 4 — Write Unit Tests (Validation)
**Files:**
- `tests/unit/test_inputs_schemas.py`
- `tests/unit/test_inputs_loaders.py`

### Test Coverage
- **Schemas**: valid creation, invalid bounds, `scale_factor` property.
- **load_assumptions**: success with 1 row; fails on missing fields.
- **load_hourly_data**: accepts 8760/8784; rejects bad row counts; rejects missing columns; rejects negative values.
- **load_degradation_table**: validates factor bounds; fails on missing year coverage.
- **load_tariff_schedule**: validates periods and hours; fails on invalid values.

### Testing Strategy
Use `tmp_path` to write minimal Excel workbooks with pandas and verify loader behavior.

---

## Step 5 — Verification
Run:
```bash
pytest tests/unit/test_inputs_*.py -v
```

---

## Files to be Modified/Created
- `src/re_storage/inputs/__init__.py`
- `src/re_storage/inputs/schemas.py`
- `src/re_storage/inputs/loaders.py`
- `tests/unit/test_inputs_schemas.py`
- `tests/unit/test_inputs_loaders.py`
