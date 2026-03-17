"""Unit tests for Excel version comparison utilities."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.compare_excel_versions import compute_kpi_deltas, discover_workbook_pair


def _touch_with_mtime(path: Path, timestamp: int) -> None:
    path.write_bytes(b"fixture")
    os.utime(path, (timestamp, timestamp))


def test_discover_workbook_pair_picks_two_newest(tmp_path: Path) -> None:
    """Discovery should return newest workbook first, then previous."""
    first = tmp_path / "old.xlsx"
    second = tmp_path / "mid.xlsx"
    third = tmp_path / "new.xlsx"

    _touch_with_mtime(first, 1_700_000_001)
    _touch_with_mtime(second, 1_700_000_101)
    _touch_with_mtime(third, 1_700_000_201)

    latest, previous = discover_workbook_pair(tmp_path)

    assert latest.name == "new.xlsx"
    assert previous.name == "mid.xlsx"


def test_compute_kpi_deltas_tags_core_material_shift() -> None:
    """Large core KPI movement should be tagged Material."""
    previous = {"project_irr": 0.05, "npv_usd": -2_600_000.0}
    latest = {"project_irr": 0.09, "npv_usd": 22_000_000.0}

    rows = {row.kpi: row for row in compute_kpi_deltas(previous, latest)}

    assert rows["project_irr"].significance == "Material"
    assert rows["npv_usd"].significance == "Material"


def test_compute_kpi_deltas_handles_none_as_structural() -> None:
    """Missing values should stay non-material and avoid delta math."""
    previous = {"calc_soc_min_kwh": None}
    latest = {"calc_soc_min_kwh": 100.0}

    row = compute_kpi_deltas(previous, latest)[0]

    assert row.significance == "Structural"
    assert row.absolute_delta is None
    assert row.relative_delta is None
