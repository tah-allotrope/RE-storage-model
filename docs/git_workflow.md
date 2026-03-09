# Git Workflow

## Branch Naming

```
feature/battery-dispatch-logic
bugfix/soc-overflow-edge-case
refactor/dppa-module-split
docs/api-reference-update
```

## Commit Messages

```
feat(battery): implement time-window arbitrage charging mode

- Add PV-to-BESS diversion based on ActivePV2BESS_Mode=1
- Respect Min_DirectPVShare constraint
- Includes unit tests for edge cases

Refs: model_architecture.md §A.2
```

## Pull Request Checklist

- [ ] All tests pass (`pytest`)
- [ ] Type checks pass (`mypy --strict`)
- [ ] Linting passes (`ruff check`)
- [ ] Docstrings complete for new functions
- [ ] Energy balance validated (if physics changes)
- [ ] Regression tests updated (if output changes)
