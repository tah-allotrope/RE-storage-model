from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from re_storage.pipeline import run_full_model, run_model_from_json
from re_storage.scenarios.runner import run_all_scenarios


ROOT = Path(__file__).resolve().parents[1]
EMIVEST_DIR = ROOT / "tests" / "data" / "projects" / "emivest"
ECOPLEXUS_XLSX = (
    ROOT / "tests" / "data" / "projects" / "AUDIT 20251201 40MW Solar ^M BESS Ecoplexus.xlsx"
)
BASELINE_DIR = ROOT / "results" / "baseline"
NEW_TARIFF_DIR = ROOT / "results" / "new_tariff"


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _strip_internal_frames(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if not key.startswith("_")}


def _build_single_json_project_dir(parent_dir: Path, json_name: str) -> Path:
    parent_dir.mkdir(parents=True, exist_ok=True)
    source_csv = EMIVEST_DIR / "Emivest additional data.csv"
    source_json = EMIVEST_DIR / json_name
    target_csv = parent_dir / source_csv.name
    target_json = parent_dir / json_name
    target_csv.write_bytes(source_csv.read_bytes())
    target_json.write_bytes(source_json.read_bytes())
    return parent_dir


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def main() -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    NEW_TARIFF_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_root:
        temp_root_path = Path(temp_root)
        emivest_2024_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2024", "Emivest.json"
        )
        emivest_baseline = run_model_from_json(emivest_2024_dir)
        _write_json(BASELINE_DIR / "emivest_tou2024.json", _strip_internal_frames(emivest_baseline))

        emivest_2026_dir = _build_single_json_project_dir(
            temp_root_path / "emivest_tou2026",
            "Emivest_TOU2026.json",
        )
        emivest_new_tariff = run_all_scenarios(project_dir=emivest_2026_dir)
        for option, result in emivest_new_tariff.items():
            _write_json(
                NEW_TARIFF_DIR / f"emivest_tou2026_option{option}.json",
                _strip_internal_frames(result),
            )

        emivest_tou2026_cycle_cap = run_all_scenarios(
            project_dir=emivest_2026_dir,
            base_params={"max_cycles_per_day": 1},
        )
        for option, result in emivest_tou2026_cycle_cap.items():
            _write_json(
                NEW_TARIFF_DIR / f"emivest_tou2026_option{option}_cyclecap1.json",
                _strip_internal_frames(result),
            )

    ecoplexus_baseline = run_full_model(ECOPLEXUS_XLSX)
    _write_json(BASELINE_DIR / "ecoplexus_tou2024.json", _strip_internal_frames(ecoplexus_baseline))

    ecoplexus_tou2026 = run_full_model(
        ECOPLEXUS_XLSX,
        base_params={"tariff_schedule_sheet": "Tariff Schedule 2026"},
    )
    _write_json(
        NEW_TARIFF_DIR / "ecoplexus_tou2026.json",
        _strip_internal_frames(ecoplexus_tou2026),
    )

    ecoplexus_tou2026_cycle_cap = run_full_model(
        ECOPLEXUS_XLSX,
        base_params={
            "tariff_schedule_sheet": "Tariff Schedule 2026",
            "max_cycles_per_day": 1,
        },
    )
    _write_json(
        NEW_TARIFF_DIR / "ecoplexus_tou2026_cyclecap1.json",
        _strip_internal_frames(ecoplexus_tou2026_cycle_cap),
    )


if __name__ == "__main__":
    main()
