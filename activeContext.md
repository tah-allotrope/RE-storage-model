# Active Context — RE-Storage Model

**Last Updated:** 2026-01-30

## 1. Current Focus

We are in **Build Mode** with verified **Core + Physics + Inputs + Settlement + Aggregation + Financial** implementations. The next steps are **Validation** plus integration/regression testing once the end-to-end pipeline is stable.

## 2. Key Reference Documents

- **AGENTS.md** — Project constitution and coding standards.
- **implementation_spec.md** — Technical blueprint and module map.
- **model_architecture.md** — Excel model logic and formulas.

## 3. Implemented Modules (Source of Truth)

### Core Layer
- `src/re_storage/core/types.py` — Type aliases, unit conventions, enums (`StrategyMode`, `ChargingMode`, `TimePeriod`, `GridChargeMode`).
- `src/re_storage/core/exceptions.py` — Domain-specific exceptions (energy balance, SoC bounds, input validation, etc.).

### Inputs Layer
- `src/re_storage/inputs/schemas.py` — Pydantic models (`SystemAssumptions`, `HourlyInputRow`, `DegradationRow`) with strict validation and `extra="forbid"`.
- `src/re_storage/inputs/loaders.py` — Excel loaders (`load_assumptions`, `load_hourly_data`, `load_degradation_table`, `load_tariff_schedule`) with DataFrame-level validation and domain exceptions.
- `src/re_storage/inputs/__init__.py` — Public exports for schemas and loaders.

### Physics Layer
- `src/re_storage/physics/solar.py`
  - PV generation scaling (`scale_generation`)
  - Direct PV consumption calculation
  - Surplus generation calculation (scalar + vectorized)

- `src/re_storage/physics/battery.py`
  - Immutable `BatteryConfig` and `BatteryState`
  - PV-to-BESS charging (time window + precharge)
  - Discharge permission logic with overlap warnings
  - SoC update with efficiency and bounds enforcement
  - Single-timestep dispatcher (`dispatch_single_timestep`)

- `src/re_storage/physics/balance.py`
  - Energy balance validation (scalar + vectorized)
  - SoC bounds validation (scalar + vectorized)
  - Power rating validation

### Settlement Layer
- `src/re_storage/settlement/dppa.py` — DPPA/CfD revenue calculations (`calculate_delivered_re`, `calculate_cfd_settlement`, `calculate_dppa_revenue`) with DPPA disabled guard and input validation.
- `src/re_storage/settlement/grid.py` — Grid expense calculations by tariff period (`calculate_energy_expense`, `calculate_bau_expense`, `calculate_re_expense`, `calculate_demand_charges`, `calculate_grid_savings`).
- `src/re_storage/settlement/__init__.py` — Public exports for DPPA and grid functions.

### Aggregation Layer
- `src/re_storage/aggregation/monthly.py` — Monthly aggregation (`aggregate_hourly_to_monthly`) with unit-suffixed columns and validation.
- `src/re_storage/aggregation/annual.py` — Year 1 totals (`calculate_year1_totals`, `calculate_total_solar_generation_mwh`, `calculate_total_dppa_revenue_usd`).
- `src/re_storage/aggregation/lifetime.py` — Lifetime projection with degradation and augmentation factors.
- `src/re_storage/aggregation/__init__.py` — Public exports for aggregation functions.

### Financial Layer
- `src/re_storage/financial/waterfall.py` — Cash flow waterfall (`build_cash_flow_waterfall`).
- `src/re_storage/financial/debt.py` — Amortization schedule + DSCR sizing (`calculate_amortization_schedule`, `size_debt_for_dscr`).
- `src/re_storage/financial/metrics.py` — XNPV/XIRR + DSCR series calculations.
- `src/re_storage/financial/__init__.py` — Public exports for financial functions.

### Testing
- `tests/unit/test_battery.py` — Battery unit tests + property-based SoC tests
- `tests/unit/test_solar.py` — Solar unit tests
- `tests/unit/test_balance.py` — Physics validation tests
- `tests/unit/test_inputs_schemas.py` — Input schema validation tests
- `tests/unit/test_inputs_loaders.py` — Input loader validation tests
- `tests/unit/test_settlement_dppa.py` — DPPA/CfD revenue calculation tests
- `tests/unit/test_settlement_grid.py` — Grid expense and savings tests
- `tests/unit/test_aggregation_monthly.py` — Monthly aggregation tests
- `tests/unit/test_aggregation_annual.py` — Annual aggregation tests
- `tests/unit/test_aggregation_lifetime.py` — Lifetime projection tests
- `tests/unit/test_financial_waterfall.py` — Waterfall tests
- `tests/unit/test_financial_debt.py` — Debt sizing tests
- `tests/unit/test_financial_metrics.py` — Metrics tests
- `tests/conftest.py` — Shared fixtures

**Latest test runs:**
- `pytest tests/unit/test_battery.py tests/unit/test_solar.py tests/unit/test_balance.py` — 96 passed
- `pytest tests/unit/test_inputs_*.py` — 25 passed
- `pytest tests/unit/test_settlement_*.py` — 18 passed
- `pytest tests/unit/test_aggregation_monthly.py tests/unit/test_aggregation_annual.py tests/unit/test_aggregation_lifetime.py` — 12 passed
- `pytest tests/unit/test_financial_metrics.py` — 5 passed

## 5. Recent Progress (2026-01-30)

### Inputs Layer Completed
- Created `inputs` package with Pydantic schemas and Excel loaders.
- Implemented strict validation for system assumptions, hourly data, degradation tables, and tariff schedules.
- Added comprehensive unit tests (25 passed) covering valid/invalid cases and edge conditions.
- Ensured immutability and defensive programming per AGENTS.md.

### Settlement Layer Completed
- Implemented DPPA/CfD revenue calculations with k-factor/kpp adjustments and consumed RE capping.
- Implemented grid expense calculations by tariff period, demand charges, and grid savings.
- Added guard behavior when DPPA is disabled (zeros + warning).
- Added comprehensive unit tests (18 passed) for formulas, validation, and edge cases.

### Documentation
- Updated `implementation.md` with detailed settlement layer plan.
- All code follows type hints, docstrings, and auditability standards.

### Aggregation Layer Completed
- Implemented monthly, annual, and lifetime aggregations with unit-suffixed columns.
- Added validation for missing columns and degradation tables.
- Added unit tests for monthly/annual/lifetime aggregation (12 passed).

### Financial Layer Completed
- Implemented cash flow waterfall, debt sizing, and return metrics.
- Added unit tests for financial waterfall, debt, and metrics.
- Fixed metrics date handling for DatetimeIndex inputs.

---

## 6. Architectural Patterns Observed

1. **Layered Architecture**: `core → inputs → physics → settlement → aggregation → financial → validation` (per `implementation_spec.md`).
2. **Immutability by Design**:
   - `BatteryConfig` is `@dataclass(frozen=True)`
   - `BatteryState` is immutable (`NamedTuple`)
3. **Physics-First Validation**:
   - Energy balance is enforced before any financial logic.
   - SoC bounds and power rating constraints throw explicit domain exceptions.
4. **Dual APIs for Performance**:
   - Scalar functions for single-step clarity.
   - Vectorized functions for batch validation over 8760 rows.
5. **Defensive Programming**:
   - Invalid inputs raise explicit exceptions.
   - Overlapping discharge conditions log warnings.

## 7. Implementation Checklist

### Phase 1: Foundation (Week 1)
- [x] Implement `core.types` and `core.exceptions`
- [x] Implement `inputs.schemas` with Pydantic models
- [x] Implement `inputs.loaders` with Excel reader
- [x] Write unit tests for input validation

### Phase 2: Physics Engine (Week 2)
- [x] Implement `physics.solar` (scale, direct consumption)
- [x] Implement `physics.battery` (dispatch logic, SoC tracking)
- [x] Implement `physics.balance` (validation)
- [x] Write property-based tests for SoC bounds

### Phase 3: Settlement (Week 3)
- [x] Implement `settlement.dppa` (CfD calculations)
- [x] Implement `settlement.grid` (tariff application)

### Phase 4: Aggregation (Week 4)
- [x] Implement `aggregation.monthly`
- [x] Implement `aggregation.annual`
- [x] Implement `aggregation.lifetime`

### Phase 5: Financial (Week 5)
- [x] Implement `financial.waterfall`
- [x] Implement `financial.debt`
- [x] Implement `financial.metrics`

### Phase 6: Integration & Validation (Week 6)
- [ ] Implement `validation.checks`
- [ ] Add integration tests (full pipeline)
- [ ] Add regression tests vs. Excel outputs
