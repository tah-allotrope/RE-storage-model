<<<<<<< C:/Users/tukum/Downloads/RE-storage-model/implementation.md
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

# Implementation Plan — Aggregation Layer (Monthly + Annual + Lifetime)

## Why this design
Aggregation is a pure rollup of hourly physics + settlement outputs, so we keep the API minimal and deterministic: monthly and annual summaries accept explicit column names with unit suffixes, and lifetime projections apply degradation tables without mutating inputs. This mirrors the Excel `Helper`/`Measures`/`Lifetime` sheets while honoring AGENTS.md unit naming rules.

---

## Step 1 — Create Aggregation Package
**Files:**
- `src/re_storage/aggregation/__init__.py`
- `src/re_storage/aggregation/monthly.py`
- `src/re_storage/aggregation/annual.py`
- `src/re_storage/aggregation/lifetime.py`

---

## Step 2 — Implement `aggregation.monthly`
**File:** `src/re_storage/aggregation/monthly.py`

### Functions & Signatures
```python
def aggregate_hourly_to_monthly(
    hourly_data: HourlyTimeSeries,
    demand_reduction_target_ratio: float,
    datetime_column: str = "datetime",
    load_column: str = "load_kw",
    bau_expense_column: str = "bau_expense_usd",
    re_expense_column: str = "re_expense_usd",
    grid_after_solar_column: str = "grid_load_after_solar_kw",
    grid_after_re_column: str = "grid_load_after_re_kw",
) -> MonthlyTimeSeries: ...
```

### Output Columns (unit suffix enforced)
- `baseline_peak_kw`
- `demand_target_kw` (baseline_peak_kw × (1 - demand_reduction_target_ratio))
- `bau_grid_expense_usd`
- `re_grid_expense_usd`
- `peak_demand_after_solar_kw`
- `peak_demand_after_re_kw`
- `grid_savings_usd` (bau_grid_expense_usd - re_grid_expense_usd)

### Validation Rules
- Required columns must exist; raise `InputValidationError` if missing.
- `demand_reduction_target_ratio` must be within [0, 1].
- `datetime_column` must be timezone-naive or uniform; month extraction via `dt.month`.
- Function must not mutate input DataFrames.

---

## Step 3 — Implement `aggregation.annual`
**File:** `src/re_storage/aggregation/annual.py`

### Functions & Signatures
```python
def calculate_total_solar_generation_mwh(
    hourly_data: HourlyTimeSeries,
    solar_gen_column: str = "solar_gen_kw",
    scale_factor: float = 1.0,
) -> float: ...

def calculate_total_dppa_revenue_usd(
    dppa_hourly: HourlyTimeSeries,
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> float: ...

def calculate_year1_totals(
    monthly_data: MonthlyTimeSeries,
    hourly_data: HourlyTimeSeries,
    dppa_hourly: HourlyTimeSeries,
    scale_factor: float,
    solar_gen_column: str = "solar_gen_kw",
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> AnnualTimeSeries: ...
```

### Output Columns (Year 1 row, unit suffix enforced)
- `year`
- `total_solar_generation_mwh`
- `total_dppa_revenue_usd`
- `total_grid_savings_usd`
- `baseline_peak_kw`
- `demand_target_kw`
- `peak_demand_after_solar_kw`
- `peak_demand_after_re_kw`

### Validation Rules
- Required columns must exist in monthly/hourly inputs.
- All energy columns must be non-negative.
- No mutation of inputs.

---

## Step 4 — Implement `aggregation.lifetime`
**File:** `src/re_storage/aggregation/lifetime.py`

### Functions & Signatures
```python
def project_lifetime_generation_mwh(
    year1_generation_mwh: float,
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> pd.Series: ...

def project_battery_capacity_kwh(
    initial_capacity_kwh: float,
    degradation_table: pd.DataFrame,
    replacement_cycle: int = 11,
    project_years: int = 25,
) -> pd.Series: ...

def build_lifetime_projection(
    year1_totals: AnnualTimeSeries,
    degradation_table: pd.DataFrame,
    initial_capacity_kwh: float,
    project_years: int = 25,
    replacement_cycle: int = 11,
) -> AnnualTimeSeries: ...
```

### Output Columns (unit suffix enforced)
- `year`
- `generation_mwh`
- `battery_capacity_kwh`
- `dppa_revenue_usd` (degraded from year1 if applicable)
- `grid_savings_usd` (degraded from year1 if applicable)

### Validation Rules
- Degradation table must cover years 1..project_years, else `DegradationTableError`.
- Degradation factor columns must be within (0, 1].
- No mutation of inputs.

---

## Step 5 — Write Unit Tests (Aggregation)
**Files:**
- `tests/unit/test_aggregation_monthly.py`
- `tests/unit/test_aggregation_annual.py`
- `tests/unit/test_aggregation_lifetime.py`

### Test Coverage
- Monthly aggregation groups by month and produces unit-suffixed columns.
- Demand target calculation uses ratio bounds and rejects invalid values.
- Annual totals compute expected MWh, DPPA revenue, and grid savings.
- Lifetime projections apply degradation factors and validate missing years.

### Testing Strategy
Use small, deterministic hourly/monthly frames (e.g., 48 hours across 2 months) to assert exact aggregations and column names.

---

## Step 6 — Verification
Run:
```bash
pytest tests/unit/test_aggregation_*.py -v
```

---

## Step 7 — Implement `financial.waterfall`
**File:** `src/re_storage/financial/waterfall.py`

### Functions & Signatures
```python
def build_cash_flow_waterfall(
    lifetime_revenue: AnnualTimeSeries,
    lifetime_opex: AnnualTimeSeries,
    debt_schedule: AnnualTimeSeries,
    capex: dict[str, float | pd.Series],
) -> AnnualTimeSeries: ...
```

### Expected Inputs (unit suffix enforced)
**lifetime_revenue** columns:
- `year`
- `dppa_revenue_usd`
- `grid_savings_usd`
- `demand_charge_savings_usd`

**lifetime_opex** columns:
- `year`
- `o_and_m_usd`
- `insurance_usd`
- `land_lease_usd`
- `management_fees_usd`
- `grid_connection_usd`
- `taxes_usd`
- `mra_contribution_usd`

**debt_schedule** columns:
- `year`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`

**capex** keys:
- `initial_capex_usd` (scalar, applied to year 0)
- `augmentation_capex_usd` (optional `pd.Series` indexed by year)

### Output Columns (unit suffix enforced)
- `year`
- `total_revenue_usd` (= dppa + grid + demand charge savings)
- `total_opex_usd` (= o_and_m + insurance + land_lease + management_fees + grid_connection)
- `ebitda_usd`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`
- `cfads_usd` (= ebitda - total debt service)
- `taxes_usd`
- `mra_contribution_usd`
- `free_cash_flow_to_equity_usd` (= cfads - taxes - mra_contribution)
- `capex_usd` (year 0 and optional augmentation)

### Validation Rules
- Required columns must exist; raise `InputValidationError` if missing.
- `year` indices must align between revenue, opex, and debt schedules.
- `capex` must include `initial_capex_usd` >= 0.
- Function must not mutate input DataFrames.

---

## Step 8 — Implement `financial.debt`
**File:** `src/re_storage/financial/debt.py`

### Functions & Signatures
```python
def calculate_amortization_schedule(
    debt_amount_usd: float,
    interest_rate_pct: float,
    tenor_years: int,
) -> AnnualTimeSeries: ...

def size_debt_for_dscr(
    ebitda_series: pd.Series,
    interest_rate_pct: float,
    tenor_years: int,
    target_dscr: float,
    initial_guess_usd: float,
) -> tuple[float, AnnualTimeSeries]: ...
```

### Output Columns (unit suffix enforced)
- `year`
- `opening_balance_usd`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`
- `closing_balance_usd`

### Validation Rules
- `debt_amount_usd`, `interest_rate_pct`, `tenor_years`, `target_dscr`, `initial_guess_usd` must be positive.
- `ebitda_series` must align with the schedule years; raise `InputValidationError` if lengths mismatch.
- Raise `DSCRConstraintError` if no feasible debt amount exists.

---

## Step 9 — Implement `financial.metrics`
**File:** `src/re_storage/financial/metrics.py`

### Functions & Signatures
```python
def calculate_npv(cashflows: pd.Series, dates: pd.Series, discount_rate_pct: float) -> float: ...

def calculate_project_irr(cashflows: pd.Series, dates: pd.Series) -> float: ...

def calculate_equity_irr(equity_cashflows: pd.Series, dates: pd.Series) -> float: ...

def calculate_dscr_series(ebitda_usd: pd.Series, debt_service_usd: pd.Series) -> pd.Series: ...
```

### Validation Rules
- `cashflows` and `dates` must be same length; include at least one positive and one negative cash flow.
- `discount_rate_pct` must be > -100.
- `debt_service_usd` must be positive for DSCR; raise `InputValidationError` if zero or negative.

---

## Step 10 — Write Unit Tests (Financial)
**Files:**
- `tests/unit/test_financial_waterfall.py`
- `tests/unit/test_financial_debt.py`
- `tests/unit/test_financial_metrics.py`

### Test Coverage
- Waterfall: revenue + opex → EBITDA → CFADS → free cash flow; capex year 0 handling.
- Debt: amortization schedule totals; DSCR sizing success + failure path.
- Metrics: XNPV/XIRR with simple cashflows; DSCR series validation.

---

## Step 11 — Verification
Run:
```bash
pytest tests/unit/test_financial_*.py -v
```

---

## Files to be Modified/Created
- `src/re_storage/aggregation/__init__.py`
- `src/re_storage/aggregation/monthly.py`
- `src/re_storage/aggregation/annual.py`
- `src/re_storage/aggregation/lifetime.py`
- `tests/unit/test_aggregation_monthly.py`
- `tests/unit/test_aggregation_annual.py`
- `tests/unit/test_aggregation_lifetime.py`
- `src/re_storage/financial/__init__.py`
- `src/re_storage/financial/waterfall.py`
- `src/re_storage/financial/debt.py`
- `src/re_storage/financial/metrics.py`
- `tests/unit/test_financial_waterfall.py`
- `tests/unit/test_financial_debt.py`
- `tests/unit/test_financial_metrics.py`
=======
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

# Implementation Plan — Aggregation Layer (Monthly + Annual + Lifetime)

## Why this design
Aggregation is a pure rollup of hourly physics + settlement outputs, so we keep the API minimal and deterministic: monthly and annual summaries accept explicit column names with unit suffixes, and lifetime projections apply degradation tables without mutating inputs. This mirrors the Excel `Helper`/`Measures`/`Lifetime` sheets while honoring AGENTS.md unit naming rules.

---

## Step 1 — Create Aggregation Package
**Files:**
- `src/re_storage/aggregation/__init__.py`
- `src/re_storage/aggregation/monthly.py`
- `src/re_storage/aggregation/annual.py`
- `src/re_storage/aggregation/lifetime.py`

---

## Step 2 — Implement `aggregation.monthly`
**File:** `src/re_storage/aggregation/monthly.py`

### Functions & Signatures
```python
def aggregate_hourly_to_monthly(
    hourly_data: HourlyTimeSeries,
    demand_reduction_target_ratio: float,
    datetime_column: str = "datetime",
    load_column: str = "load_kw",
    bau_expense_column: str = "bau_expense_usd",
    re_expense_column: str = "re_expense_usd",
    grid_after_solar_column: str = "grid_load_after_solar_kw",
    grid_after_re_column: str = "grid_load_after_re_kw",
) -> MonthlyTimeSeries: ...
```

### Output Columns (unit suffix enforced)
- `baseline_peak_kw`
- `demand_target_kw` (baseline_peak_kw × (1 - demand_reduction_target_ratio))
- `bau_grid_expense_usd`
- `re_grid_expense_usd`
- `peak_demand_after_solar_kw`
- `peak_demand_after_re_kw`
- `grid_savings_usd` (bau_grid_expense_usd - re_grid_expense_usd)

### Validation Rules
- Required columns must exist; raise `InputValidationError` if missing.
- `demand_reduction_target_ratio` must be within [0, 1].
- `datetime_column` must be timezone-naive or uniform; month extraction via `dt.month`.
- Function must not mutate input DataFrames.

---

## Step 3 — Implement `aggregation.annual`
**File:** `src/re_storage/aggregation/annual.py`

### Functions & Signatures
```python
def calculate_total_solar_generation_mwh(
    hourly_data: HourlyTimeSeries,
    solar_gen_column: str = "solar_gen_kw",
    scale_factor: float = 1.0,
) -> float: ...

def calculate_total_dppa_revenue_usd(
    dppa_hourly: HourlyTimeSeries,
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> float: ...

def calculate_year1_totals(
    monthly_data: MonthlyTimeSeries,
    hourly_data: HourlyTimeSeries,
    dppa_hourly: HourlyTimeSeries,
    scale_factor: float,
    solar_gen_column: str = "solar_gen_kw",
    total_dppa_column: str = "total_dppa_revenue_usd",
) -> AnnualTimeSeries: ...
```

### Output Columns (Year 1 row, unit suffix enforced)
- `year`
- `total_solar_generation_mwh`
- `total_dppa_revenue_usd`
- `total_grid_savings_usd`
- `baseline_peak_kw`
- `demand_target_kw`
- `peak_demand_after_solar_kw`
- `peak_demand_after_re_kw`

### Validation Rules
- Required columns must exist in monthly/hourly inputs.
- All energy columns must be non-negative.
- No mutation of inputs.

---

## Step 4 — Implement `aggregation.lifetime`
**File:** `src/re_storage/aggregation/lifetime.py`

### Functions & Signatures
```python
def project_lifetime_generation_mwh(
    year1_generation_mwh: float,
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> pd.Series: ...

def project_battery_capacity_kwh(
    initial_capacity_kwh: float,
    degradation_table: pd.DataFrame,
    replacement_cycle: int = 11,
    project_years: int = 25,
) -> pd.Series: ...

def build_lifetime_projection(
    year1_totals: AnnualTimeSeries,
    degradation_table: pd.DataFrame,
    initial_capacity_kwh: float,
    project_years: int = 25,
    replacement_cycle: int = 11,
) -> AnnualTimeSeries: ...
```

### Output Columns (unit suffix enforced)
- `year`
- `generation_mwh`
- `battery_capacity_kwh`
- `dppa_revenue_usd` (degraded from year1 if applicable)
- `grid_savings_usd` (degraded from year1 if applicable)

### Validation Rules
- Degradation table must cover years 1..project_years, else `DegradationTableError`.
- Degradation factor columns must be within (0, 1].
- No mutation of inputs.

---

## Step 5 — Write Unit Tests (Aggregation)
**Files:**
- `tests/unit/test_aggregation_monthly.py`
- `tests/unit/test_aggregation_annual.py`
- `tests/unit/test_aggregation_lifetime.py`

### Test Coverage
- Monthly aggregation groups by month and produces unit-suffixed columns.
- Demand target calculation uses ratio bounds and rejects invalid values.
- Annual totals compute expected MWh, DPPA revenue, and grid savings.
- Lifetime projections apply degradation factors and validate missing years.

### Testing Strategy
Use small, deterministic hourly/monthly frames (e.g., 48 hours across 2 months) to assert exact aggregations and column names.

---

## Step 6 — Verification
Run:
```bash
pytest tests/unit/test_aggregation_*.py -v
```

---

## Step 7 — Implement `financial.waterfall`
**File:** `src/re_storage/financial/waterfall.py`

### Functions & Signatures
```python
def build_cash_flow_waterfall(
    lifetime_revenue: AnnualTimeSeries,
    lifetime_opex: AnnualTimeSeries,
    debt_schedule: AnnualTimeSeries,
    capex: dict[str, float | pd.Series],
) -> AnnualTimeSeries: ...
```

### Expected Inputs (unit suffix enforced)
**lifetime_revenue** columns:
- `year`
- `dppa_revenue_usd`
- `grid_savings_usd`
- `demand_charge_savings_usd`

**lifetime_opex** columns:
- `year`
- `o_and_m_usd`
- `insurance_usd`
- `land_lease_usd`
- `management_fees_usd`
- `grid_connection_usd`
- `taxes_usd`
- `mra_contribution_usd`

**debt_schedule** columns:
- `year`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`

**capex** keys:
- `initial_capex_usd` (scalar, applied to year 0)
- `augmentation_capex_usd` (optional `pd.Series` indexed by year)

### Output Columns (unit suffix enforced)
- `year`
- `total_revenue_usd` (= dppa + grid + demand charge savings)
- `total_opex_usd` (= o_and_m + insurance + land_lease + management_fees + grid_connection)
- `ebitda_usd`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`
- `cfads_usd` (= ebitda - total debt service)
- `taxes_usd`
- `mra_contribution_usd`
- `free_cash_flow_to_equity_usd` (= cfads - taxes - mra_contribution)
- `capex_usd` (year 0 and optional augmentation)

### Validation Rules
- Required columns must exist; raise `InputValidationError` if missing.
- `year` indices must align between revenue, opex, and debt schedules.
- `capex` must include `initial_capex_usd` >= 0.
- Function must not mutate input DataFrames.

---

## Step 8 — Implement `financial.debt`
**File:** `src/re_storage/financial/debt.py`

### Functions & Signatures
```python
def calculate_amortization_schedule(
    debt_amount_usd: float,
    interest_rate_pct: float,
    tenor_years: int,
) -> AnnualTimeSeries: ...

def size_debt_for_dscr(
    ebitda_series: pd.Series,
    interest_rate_pct: float,
    tenor_years: int,
    target_dscr: float,
    initial_guess_usd: float,
) -> tuple[float, AnnualTimeSeries]: ...
```

### Output Columns (unit suffix enforced)
- `year`
- `opening_balance_usd`
- `interest_usd`
- `principal_usd`
- `total_debt_service_usd`
- `closing_balance_usd`

### Validation Rules
- `debt_amount_usd`, `interest_rate_pct`, `tenor_years`, `target_dscr`, `initial_guess_usd` must be positive.
- `ebitda_series` must align with the schedule years; raise `InputValidationError` if lengths mismatch.
- Raise `DSCRConstraintError` if no feasible debt amount exists.

---

## Step 9 — Implement `financial.metrics`
**File:** `src/re_storage/financial/metrics.py`

### Functions & Signatures
```python
def calculate_npv(cashflows: pd.Series, dates: pd.Series, discount_rate_pct: float) -> float: ...

def calculate_project_irr(cashflows: pd.Series, dates: pd.Series) -> float: ...

def calculate_equity_irr(equity_cashflows: pd.Series, dates: pd.Series) -> float: ...

def calculate_dscr_series(ebitda_usd: pd.Series, debt_service_usd: pd.Series) -> pd.Series: ...
```

### Validation Rules
- `cashflows` and `dates` must be same length; include at least one positive and one negative cash flow.
- `discount_rate_pct` must be > -100.
- `debt_service_usd` must be positive for DSCR; raise `InputValidationError` if zero or negative.

---

## Step 10 — Write Unit Tests (Financial)
**Files:**
- `tests/unit/test_financial_waterfall.py`
- `tests/unit/test_financial_debt.py`
- `tests/unit/test_financial_metrics.py`

### Test Coverage
- Waterfall: revenue + opex → EBITDA → CFADS → free cash flow; capex year 0 handling.
- Debt: amortization schedule totals; DSCR sizing success + failure path.
- Metrics: XNPV/XIRR with simple cashflows; DSCR series validation.

---

## Step 11 — Verification
Run:
```bash
pytest tests/unit/test_financial_*.py -v
```

---

## Files to be Modified/Created
- `src/re_storage/aggregation/__init__.py`
- `src/re_storage/aggregation/monthly.py`
- `src/re_storage/aggregation/annual.py`
- `src/re_storage/aggregation/lifetime.py`
- `tests/unit/test_aggregation_monthly.py`
- `tests/unit/test_aggregation_annual.py`
- `tests/unit/test_aggregation_lifetime.py`
- `src/re_storage/financial/__init__.py`
- `src/re_storage/financial/waterfall.py`
- `src/re_storage/financial/debt.py`
- `src/re_storage/financial/metrics.py`
- `tests/unit/test_financial_waterfall.py`
- `tests/unit/test_financial_debt.py`
- `tests/unit/test_financial_metrics.py`

# Implementation Plan — Validation & Integration

## Why this design
Validation is a cross-cutting concern that should aggregate physics, settlement, and financial checks into a single, auditable warnings list. Integration and regression tests then prove that the full pipeline behaves correctly without mutating inputs or silently skipping failures.

---

## Step 1 — Implement `validation.checks`
**Files:**
- `src/re_storage/validation/__init__.py`
- `src/re_storage/validation/checks.py`

### Functions & Signatures
```python
def validate_energy_balance_series(
    hourly_results: HourlyTimeSeries,
    solar_gen_column: str = "solar_gen_kwh",
    direct_consumption_column: str = "direct_consumption_kwh",
    charged_column: str = "charged_kwh",
    surplus_column: str = "surplus_kwh",
    tolerance: float = 0.001,
) -> list[str]: ...

def validate_soc_bounds_series(
    hourly_results: HourlyTimeSeries,
    max_capacity_kwh: float,
    soc_column: str = "soc_kwh",
    tolerance: float = 0.001,
) -> list[str]: ...

def validate_dppa_revenue(
    lifetime_results: pd.DataFrame,
    dppa_enabled: bool,
    revenue_column: str = "dppa_revenue_usd",
) -> list[str]: ...

def validate_degradation_coverage(
    degradation_table: pd.DataFrame,
    project_years: int = 25,
) -> list[str]: ...

def validate_augmentation_funding(
    lifetime_results: pd.DataFrame,
    augmentation_years: list[int] | None = None,
    augmentation_capex_column: str = "augmentation_capex_usd",
    mra_balance_column: str = "mra_balance_usd",
) -> list[str]: ...

def validate_full_model(
    hourly_results: HourlyTimeSeries,
    monthly_results: MonthlyTimeSeries,
    lifetime_results: pd.DataFrame,
    assumptions: SystemAssumptions,
    degradation_table: pd.DataFrame | None = None,
    project_years: int = 25,
) -> list[str]: ...
```

### Validation Rules
- Use vectorized physics validators for energy balance and SoC bounds.
- Return warnings (not exceptions) for failed checks to preserve full auditability.
- Raise `InputValidationError` when required columns are missing.

---

## Step 2 — Unit Tests (Validation)
**File:** `tests/unit/test_validation_checks.py`

### Coverage
- Balanced/imbalanced energy checks
- SoC bounds violations
- DPPA revenue warnings when enabled but zero
- Degradation coverage warnings for missing years
- Augmentation funding warnings when MRA is insufficient

---

## Step 3 — Integration Tests
**Files:**
- `tests/integration/test_full_pipeline.py`

### Scenarios
- End-to-end pipeline on a small synthetic dataset
- DPPA disabled behavior in the pipeline
- Leap-year hourly inputs (8784 rows) for monthly aggregation

---

## Step 4 — Regression Test Scaffolding
**File:** `tests/regression/test_excel_comparison.py`

### Expected KPIs (Excel Reference)
- Project IRR: 5.07%
- Equity IRR: 4.64%
- Unlevered IRR: 8.83%
- NPV: -$2.65M

Regression tests should be skipped with a clear message if reference fixtures
are not present in `tests/data/`.

---

## Step 5 — Verification
Run:
```bash
pytest tests/unit/test_validation_checks.py -v
pytest tests/integration/ -v
pytest tests/regression/ -v
```

---

## Files to be Modified/Created
- `src/re_storage/validation/__init__.py`
- `src/re_storage/validation/checks.py`
- `tests/unit/test_validation_checks.py`
- `tests/integration/__init__.py`
- `tests/integration/test_full_pipeline.py`
- `tests/regression/__init__.py`
- `tests/regression/test_excel_comparison.py`
<<<<<<< C:/Users/tukum/Downloads/RE-storage-model/implementation.md
>>>>>>> C:/Users/tukum/.windsurf/worktrees/RE-storage-model/RE-storage-model-86eaba68/implementation.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/RE-storage-model/RE-storage-model-86eaba68/implementation.md
