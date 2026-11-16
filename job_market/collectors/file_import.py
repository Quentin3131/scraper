"""CSV/JSON importer for user-provided or otherwise authorized job exports."""

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from job_market.collectors.base import CollectorError
from job_market.schemas import JobAdInput


class FileImportCollector:
    """Read local files only; this adapter performs no network access."""

    def __init__(self, path: Path, source_name: str = "file_import") -> None:
        if path.suffix.lower() not in {".csv", ".json"}:
            raise ValueError("file import supports only .csv and .json files")
        self.path = path
        self.source_name = source_name

    def collect(self) -> Iterator[JobAdInput]:
        if not self.path.is_file():
            raise CollectorError(f"import file does not exist: {self.path}")
        records = self._read_records()
        for index, record in enumerate(records, start=2):
            payload = dict(record)
            payload["source"] = payload.get("source") or self.source_name
            try:
                yield JobAdInput.model_validate(payload)
            except ValidationError as error:
                raise CollectorError(f"invalid record near row {index} in {self.path}: {error}") from error

    def _read_records(self) -> list[dict[str, Any]]:
        try:
            if self.path.suffix.lower() == ".csv":
                with self.path.open(newline="", encoding="utf-8-sig") as file:
                    return [dict(row) for row in csv.DictReader(file)]
            with self.path.open(encoding="utf-8") as file:
                document = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as error:
            raise CollectorError(f"could not read {self.path}: {error}") from error
        if isinstance(document, dict):
            document = document.get("jobs")
        if not isinstance(document, list) or not all(isinstance(item, dict) for item in document):
            raise CollectorError("JSON import must be a list of objects or an object containing a 'jobs' list")
        return document
