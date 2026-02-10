# RE-Storage: Vietnam Solar + BESS Financial Model

A Python simulation engine for modeling solar PV and battery energy storage systems (BESS) for project finance applications in Vietnam.

## Philosophy

> **"Physics First, Finance Second."**

Energy balance (kWh) is validated before applying tariffs ($). All calculations are auditable and reproducible.

## Project Structure

```
RE-storage-model/
├── AGENTS.md                    # Project constitution & coding standards
├── implementation_spec.md       # Technical architecture blueprint
├── model_architecture.md        # Excel model domain logic (reference)
├── pyproject.toml               # Project config & dependencies
├── src/
│   └── re_storage/
│       ├── core/                # Domain types & exceptions
│       ├── inputs/              # Input loading & Pydantic validation
│       ├── physics/             # Solar generation, battery dispatch, energy balance
│       ├── settlement/          # DPPA/CfD revenue, grid charges & savings
│       ├── aggregation/         # Hourly → Monthly → Annual → Lifetime
│       ├── financial/           # Cash flow waterfall, debt sizing, IRR/NPV
│       └── validation/          # Cross-cutting validation checks
├── tests/
│   ├── unit/                    # Unit tests by module
│   ├── integration/             # End-to-end pipeline tests
│   ├── regression/              # Excel comparison tests
│   └── data/                    # Test fixtures
├── scripts/                     # One-off analysis & investigation scripts
├── docs/                        # Working documents & reports
├── data/                        # Input data files (Excel models)
└── notebooks/                   # Exploration & debugging notebooks
```

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                    # Run all tests
pytest tests/unit/        # Unit tests only
pytest -v --tb=short      # Verbose with short tracebacks
```

### Type Checking & Linting

```bash
mypy --strict src/
ruff check src/ tests/
black --check src/ tests/
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Core Computation | pandas + numpy |
| Configuration | pydantic |
| Testing | pytest + hypothesis |
| Type Checking | mypy --strict |
| Formatting | black + isort + ruff |

## License

MIT
