"""Stable CSV and JSON exports for reproducible analysis outputs."""

import csv
import json
from pathlib import Path
from typing import Any


def export_rows(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.casefold() == ".json":
        path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
        return
    if path.suffix.casefold() != ".csv":
        raise ValueError("export path must end in .csv or .json")
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
