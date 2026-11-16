"""Evaluate the checked-in labeled fixture set without external services."""

import json
from pathlib import Path

from job_market.evaluation import LabeledPosting, evaluate


def main() -> None:
    path = Path("data/evaluation_labels.json")
    records = [
        LabeledPosting(
            title=item["title"],
            description=item["description"],
            expected_skills=frozenset(item["expected_skills"]),
            expected_seniority=item["expected_seniority"],
        )
        for item in json.loads(path.read_text(encoding="utf-8"))
    ]
    print(json.dumps(evaluate(records).__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
