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

# Implementation Plan — Settlement Layer (DPPA + Grid)

## Why this design
The settlement layer should be **pure, auditable transformations** over hourly time series. We keep functions small and explicit so each formula maps cleanly to the DPPA and grid logic in `model_architecture.md`, while preserving the “Physics First” ordering by only consuming already-balanced energy results.

---

## Step 1 — Create Settlement Package
**Files:**
- `src/re_storage/settlement/__init__.py`
- `src/re_storage/settlement/dppa.py`
- `src/re_storage/settlement/grid.py`

---

## Step 2 — Implement `settlement.dppa`
**File:** `src/re_storage/settlement/dppa.py`

### Functions & Signatures
```python
def calculate_delivered_re(
    net_gen_kwh: float,
    k_factor: float,
    kpp: float,
    delta: float = 1.0,
) -> float: ...

def calculate_consumed_re(
    delivered_re_kwh: float,
    load_kwh: float,
) -> float: ...

def calculate_market_revenue(
    net_gen_kwh: float,
    fmp_usd_per_kwh: float,
) -> float: ...

def calculate_cfd_settlement(
    consumed_re_kwh: float,
    strike_price_usd_per_kwh: float,
    spot_price_usd_per_kwh: float,
) -> float: ...

def calculate_total_dppa_revenue(
    market_revenue_usd: float,
    cfd_settlement_usd: float,
) -> float: ...

def calculate_dppa_revenue(
    hourly_data: HourlyTimeSeries,
    assumptions: SystemAssumptions,
    net_gen_column: str = "net_gen_for_dppa_kwh",
    load_column: str = "load_kwh",
    fmp_column: str = "fmp_usd_per_kwh",
    delta: float = 1.0,
) -> pd.DataFrame: ...
```

### Validation Rules
- Fail on negative energy inputs (kWh < 0).
- `calculate_dppa_revenue` must **not mutate** input DataFrames.
- When `assumptions.dppa_enabled` is `False`, return zeroed revenue columns and log a warning.

---

## Step 3 — Implement `settlement.grid`
**File:** `src/re_storage/settlement/grid.py`

### Functions & Signatures
```python
def calculate_energy_expense(
    energy_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series: ...

def calculate_bau_expense(
    load_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series: ...

def calculate_re_expense(
    grid_load_after_re_kwh: pd.Series,
    time_period: pd.Series,
    tariff_rates_usd_per_kwh: dict[TimePeriod, float],
) -> pd.Series: ...

def calculate_demand_charges(
    peak_demand_kw: float,
    demand_charge_rate_usd_per_kw: float,
) -> float: ...

def calculate_grid_savings(
    bau_expense_usd: pd.Series,
    re_expense_usd: pd.Series,
) -> pd.Series: ...
```

### Validation Rules
- Reject negative energy inputs.
- Ensure time period values are valid `TimePeriod` enums and covered by the tariff map.

---

## Step 4 — Write Unit Tests (Settlement)
**Files:**
- `tests/unit/test_settlement_dppa.py`
- `tests/unit/test_settlement_grid.py`

### Test Coverage
- DPPA formulas (delivered, consumed, market revenue, CfD, total).
- `calculate_dppa_revenue` behavior when DPPA is disabled (zeros + warning).
- Grid expenses by tariff period, demand charges, and grid savings.
- Validation errors for negative energy and invalid tariff periods.

---

## Step 5 — Verification
Run:
```bash
pytest tests/unit/test_settlement_*.py -v
```

---

## Files to be Modified/Created
- `src/re_storage/settlement/__init__.py`
- `src/re_storage/settlement/dppa.py`
- `src/re_storage/settlement/grid.py`
- `tests/unit/test_settlement_dppa.py`
- `tests/unit/test_settlement_grid.py`
