# Active Context — RE-Storage Model

**Last Updated:** 2026-01-29

## 1. Current Focus

We are in **Build Mode** with a verified **Core + Physics** implementation. The next steps are the **Inputs** and **Settlement** layers, followed by Aggregation and Financial layers once physics validations remain stable.

## 2. Key Reference Documents

- **AGENTS.md** — Project constitution and coding standards.
- **implementation_spec.md** — Technical blueprint and module map.
- **model_architecture.md** — Excel model logic and formulas.

## 3. Implemented Modules (Source of Truth)

### Core Layer
- `src/re_storage/core/types.py` — Type aliases, unit conventions, enums (`StrategyMode`, `ChargingMode`, `TimePeriod`, `GridChargeMode`).
- `src/re_storage/core/exceptions.py` — Domain-specific exceptions (energy balance, SoC bounds, input validation, etc.).

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

### Testing
- `tests/unit/test_battery.py` — Battery unit tests + property-based SoC tests
- `tests/unit/test_solar.py` — Solar unit tests
- `tests/unit/test_balance.py` — Physics validation tests
- `tests/conftest.py` — Shared fixtures

**Latest test run:** `pytest tests/` — **96 passed**

## 4. Architectural Patterns Observed

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

## 5. Implementation Checklist

### Phase 1: Foundation (Week 1)
- [x] Implement `core.types` and `core.exceptions`
- [ ] Implement `inputs.schemas` with Pydantic models
- [ ] Implement `inputs.loaders` with Excel reader
- [ ] Write unit tests for input validation

### Phase 2: Physics Engine (Week 2)
- [x] Implement `physics.solar` (scale, direct consumption)
- [x] Implement `physics.battery` (dispatch logic, SoC tracking)
- [x] Implement `physics.balance` (validation)
- [x] Write property-based tests for SoC bounds

### Phase 3: Settlement (Week 3)
- [ ] Implement `settlement.dppa` (CfD calculations)
- [ ] Implement `settlement.grid` (tariff application)

### Phase 4: Aggregation (Week 4)
- [ ] Implement `aggregation.monthly`
- [ ] Implement `aggregation.annual`
- [ ] Implement `aggregation.lifetime`

### Phase 5: Financial (Week 5)
- [ ] Implement `financial.waterfall`
- [ ] Implement `financial.debt`
- [ ] Implement `financial.metrics`

### Phase 6: Integration & Validation (Week 6)
- [ ] Implement `validation.checks`
- [ ] Add integration tests (full pipeline)
- [ ] Add regression tests vs. Excel outputs
