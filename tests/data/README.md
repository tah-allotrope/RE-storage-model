# Regression Test Fixtures

## Directory Layout

```
tests/data/
├── projects/          # Place your Excel input files here (.xlsx)
│   ├── project_01.xlsx
│   ├── project_02.xlsx
│   └── ...
├── references/        # Auto-generated JSON reference KPIs (one per project)
│   ├── project_01.json
│   ├── project_02.json
│   └── ...
└── README.md          # This file
```

## Setup Steps

### 1. Place Excel Files

Copy your project Excel files into `tests/data/projects/`. Each file must
follow the standard sheet structure: `Assumption`, `Data Input`, `Loss`,
and optionally `Tariff Schedule`.

### 2. Extract Reference KPIs

Run the extraction script to read pre-calculated values from the Excel
files and save them as JSON:

```bash
python scripts/extract_excel_kpis.py tests/data/projects/*.xlsx
```

**Important:** `openpyxl` reads cached formula results. If cells show `None`,
re-open each Excel file, press **Ctrl+Shift+F9** to recalculate all formulas,
save, and re-run the extraction script.

### 3. Run Regression Tests

```bash
pytest tests/regression/ -v
```

The tests auto-discover all `.xlsx` / `.json` pairs and compare Python
model outputs against the Excel references at multiple layers:

- **Physics:** Solar generation sum, SoC min/max
- **Aggregation:** Year 1 totals (generation, DPPA revenue, grid savings)
- **Financial:** Project IRR, Equity IRR, Unlevered IRR, NPV, DSCR

## Tolerance Tiers (AGENTS.md §4.3)

| Metric | Tolerance |
|--------|-----------|
| Energy (kWh/MWh) | ±0.01% relative |
| Revenue/Cost ($) | ±0.01% relative |
| IRR (%) | ±0.0001 absolute |
| DSCR (ratio) | ±0.001 absolute |
