"""Prepare the Firebase functions source tree for deployment."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE_DIR = ROOT / "src" / "re_storage"
FUNCTIONS_DIR = ROOT / "web" / "functions"
TARGET_PACKAGE_DIR = FUNCTIONS_DIR / "re_storage"


def _ignore_copy_dir(_: str, names: list[str]) -> set[str]:
    ignored_names = {"__pycache__"}
    ignored_suffixes = (".pyc", ".pyo")
    return {
        name
        for name in names
        if name in ignored_names or any(name.endswith(suffix) for suffix in ignored_suffixes)
    }


def main() -> None:
    if not SOURCE_PACKAGE_DIR.exists():
        raise FileNotFoundError(f"Missing source package directory: {SOURCE_PACKAGE_DIR}")

    if TARGET_PACKAGE_DIR.exists():
        shutil.rmtree(TARGET_PACKAGE_DIR)

    shutil.copytree(SOURCE_PACKAGE_DIR, TARGET_PACKAGE_DIR, ignore=_ignore_copy_dir)
    print(f"Vendored {SOURCE_PACKAGE_DIR} -> {TARGET_PACKAGE_DIR}")


if __name__ == "__main__":
    main()
