# AGENTS.md

RE-Storage is a financial model simulation engine for renewable energy + battery storage projects.

## Commands

| Task | Command |
|------|---------|
| Run tests | `pytest` |
| Type check | `mypy --strict` |
| Lint | `ruff check` |
| All checks | `pytest && mypy --strict && ruff check` |

## Philosophy

**Physics First, Finance Second.** Energy balance (kWh) must validate before tariffs ($).

## Project Structure

```
src/re_storage/
├── core/         # Domain types, exceptions
├── inputs/       # Input loading, Pydantic schemas
├── physics/      # Energy simulation (solar, battery, balance)
├── settlement/   # Revenue (DPPA, grid)
├── aggregation/  # Hourly → Monthly → Annual → Lifetime
├── financial/    # Cash flow, debt, metrics (IRR, NPV, DSCR)
└── validation/   # Energy balance checks, warnings
```

## Detailed Guides

- [Coding Standards](docs/coding_standards.md) — Type hints, immutability, docstrings, naming
- [Testing](docs/testing.md) — Unit, property-based, regression tests
- [Git Workflow](docs/git_workflow.md) — Branch naming, commits, PR checklist

## Communication

When uncertain: state the uncertainty, reference the source, propose options, ask for clarification.
