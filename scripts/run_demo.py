"""Run the complete local demo pipeline using clearly labeled sample data."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_market.analysis.metrics import skill_frequency
from job_market.collectors.file_import import FileImportCollector
from job_market.config import Settings
from job_market.processing.enrichment import enrich_job
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import Job


def main() -> None:
    settings = Settings(database_url="sqlite:///data/demo.db")
    engine = create_database_engine(settings)
    initialize_database(engine)
    ingest_ads(engine, FileImportCollector(Path("data/demo_jobs.json"), "labeled_demo_data").collect(), "labeled_demo_data")
    with Session(engine) as session:
        job_ids = list(session.scalars(select(Job.id)))
    for job_id in job_ids:
        enrich_job(engine, job_id)
    print(json.dumps([metric.__dict__ for metric in skill_frequency(engine)], indent=2))


if __name__ == "__main__":
    main()
