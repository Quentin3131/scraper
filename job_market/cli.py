"""Minimal CLI for bootstrapping a local database."""

import argparse
import json
from pathlib import Path

from job_market.analysis.export import export_rows
from job_market.analysis.metrics import AnalysisScope, skill_cooccurrence, skill_frequency
from job_market.analysis.quality import data_quality_report
from job_market.collectors.file_import import FileImportCollector
from job_market.config import Settings
from job_market.processing.enrichment import enrich_job
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads


def main() -> None:
    parser = argparse.ArgumentParser(prog="job-market")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("init", "import", "enrich", "analyze", "evaluate"),
        default="init",
    )
    parser.add_argument("path", nargs="?", type=Path, help="CSV or JSON file for the import command")
    parser.add_argument("--database-url", help="Override the configured database URL")
    parser.add_argument("--source", default="file_import", help="Source label for imported records")
    parser.add_argument("--job-id", type=int, help="Canonical job ID for the enrich command")
    parser.add_argument("--export", type=Path, help="CSV or JSON output for the analyze command")
    args = parser.parse_args()
    settings = Settings(database_url=args.database_url) if args.database_url else Settings.from_environment()
    engine = create_database_engine(settings)
    initialize_database(engine)
    if args.command == "import":
        if args.path is None:
            parser.error("the import command requires a CSV or JSON path")
        event = ingest_ads(engine, FileImportCollector(args.path, args.source).collect(), args.source)
        print(f"Imported {event.records_accepted} new records ({event.records_seen} seen)")
    elif args.command == "enrich":
        if args.job_id is None:
            parser.error("the enrich command requires --job-id")
        count = enrich_job(engine, args.job_id)
        print(f"Extracted {count} skill requirements for job {args.job_id}")
    elif args.command == "analyze":
        scope = AnalysisScope(include_ambiguous=False)
        output = {
            "skills": [metric.__dict__ for metric in skill_frequency(engine, scope)],
            "cooccurrence": [metric.__dict__ for metric in skill_cooccurrence(engine, scope)],
            "quality": data_quality_report(engine),
        }
        if args.export:
            args.export.parent.mkdir(parents=True, exist_ok=True)
            if args.export.suffix.casefold() == ".csv":
                export_rows(output["skills"], args.export)
            elif args.export.suffix.casefold() == ".json":
                args.export.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
            else:
                parser.error("analysis export must end in .csv or .json")
            print(f"Exported analysis to {args.export}")
        else:
            print(json.dumps(output, indent=2, sort_keys=True))
    elif args.command == "evaluate":
        from job_market.evaluation import LabeledPosting, evaluate

        labels_path = args.path or Path("data/evaluation_labels.json")
        records = [
            LabeledPosting(
                title=item["title"],
                description=item["description"],
                expected_skills=frozenset(item["expected_skills"]),
                expected_seniority=item["expected_seniority"],
            )
            for item in json.loads(labels_path.read_text(encoding="utf-8"))
        ]
        print(json.dumps(evaluate(records).__dict__, indent=2, sort_keys=True))
    else:
        print(f"Initialized {settings.database_url}")


if __name__ == "__main__":
    main()
