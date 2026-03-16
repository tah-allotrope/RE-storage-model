# Fixture Layout

Use this layout for Excel regression fixtures:

```
tests/data/
├── projects/      # Excel files (.xlsx)
└── references/    # Extracted KPI JSON files
```

Rules:

- Store each project workbook in `tests/data/projects/`.
- Keep reference filename stem equal to workbook stem.
- Ensure one-to-one pairing for auto-discovery in regression tests.
- Keep project files and references committed together.

Core command:

```bash
python scripts/extract_excel_kpis.py tests/data/projects/*.xlsx
```
