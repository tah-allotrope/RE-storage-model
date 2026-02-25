# Active Context — RE-Storage Model

**Last Updated:** 2026-02-25

## 1. Current Focus

We are in **Regression Testing Mode** with a fully operational end-to-end pipeline (`run_full_model`) and a multi-project regression test harness validated against the production Excel model. All 175 tests pass (169 unit + 3 integration + 3 regression).

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
- `src/re_storage/inputs/loaders.py` — Excel loaders with real-format adapters:
  - `load_assumptions` — flat single-row loader (for preprocessed sheets)
  - `load_assumptions_from_cells` — multi-region cell-based loader (for production Excel files)
  - `load_hourly_data` — with auto column rename (`SimulationProfile_kW` → `simulation_profile_kw`, etc.)
  - `load_degradation_table` — with Loss sheet header detection and column rename
  - `load_tariff_schedule` — tariff period loader
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

### Validation Layer
- `src/re_storage/validation/checks.py` — Validation warnings for energy balance, SoC bounds, DPPA revenue, degradation coverage, and augmentation funding.
- `src/re_storage/validation/__init__.py` — Public exports for validation checks.

### Pipeline
- `src/re_storage/pipeline.py` — End-to-end `run_full_model(excel_path)` entrypoint wiring: inputs → physics → settlement → aggregation → financial → metrics. Returns flat `dict[str, float]` of KPIs.

### Scripts
- `scripts/extract_excel_kpis.py` — Reference KPI extractor from Excel files using `openpyxl data_only=True`. Reads Financial sheet cells, Calc column stats, and Measures sheet labels. Outputs JSON to `tests/data/references/`.

### Testing
- `tests/unit/` — 169 unit tests across all modules
- `tests/integration/test_full_pipeline.py` — End-to-end pipeline integration tests (3 tests)
- `tests/regression/test_excel_comparison.py` — Parametrized multi-project, multi-layer regression tests:
  - Auto-discovers `.xlsx` in `tests/data/projects/` + `.json` in `tests/data/references/`
  - `test_all_kpis` — compares all available KPIs
  - `test_physics_layer` — isolates solar gen + SoC tracking
  - `test_financial_kpis` — isolates IRR/NPV/DSCR
  - Tolerance tiers: Energy ±0.01%, Revenue ±0.01%, IRR ±0.0001, DSCR ±0.001
- `tests/data/projects/` — Excel input files for regression testing
- `tests/data/references/` — JSON reference KPIs extracted from Excel
- `tests/conftest.py` — Shared fixtures

**Latest test run (2026-02-25):**
- `pytest tests/` — **175 passed** (169 unit + 3 integration + 3 regression)

## 5. Recent Progress

### Regression Test Harness (2026-02-25)
- Built `scripts/extract_excel_kpis.py` for automated Excel KPI extraction.
- Built `src/re_storage/pipeline.py` with `run_full_model()` entrypoint.
- Rewrote `tests/regression/test_excel_comparison.py` with parametrized multi-project, multi-layer comparison.
- Added `load_assumptions_from_cells()` to handle real Excel multi-region Assumption sheet layout.
- Added column normalization for Data Input sheet (`SimulationProfile_kW` → `simulation_profile_kw`).
- Added Loss sheet header detection and column rename (`PV` → `pv_factor`, etc.).
- Fixed k-factor label matching (exact match for short labels to avoid "k" matching "Ca_peak").
- Fixed PV2BESS Mode 0: all surplus charges BESS at any hour with `min_direct_pv_share=1.0` and `active_pv2bess_share=1.0`.
- Validated against production Excel file: **all 3 regression tests pass** (physics, financial, all_kpis).

### Previous Milestones
- Core + Physics + Inputs + Settlement + Aggregation + Financial + Validation layers implemented and tested.
- Integration tests for synthetic pipeline runs and leap-year aggregation.

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
- [x] Implement `validation.checks`
- [x] Add integration tests (full pipeline)
- [x] Add regression tests vs. Excel outputs

### Phase 7: Regression Harness (Week 7)
- [x] Build `extract_excel_kpis.py` script
- [x] Build `pipeline.py` with `run_full_model`
- [x] Add real-format Excel loaders (Assumption, Data Input, Loss)
- [x] Validate against production Excel — 175/175 tests pass
- [ ] Add remaining 9 project Excel files and validate
