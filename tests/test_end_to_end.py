import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_market.analysis.metrics import skill_frequency
from job_market.collectors.file_import import FileImportCollector
from job_market.config import Settings
from job_market.processing.enrichment import enrich_job
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import Job


def test_demo_pipeline_imports_enriches_and_analyzes(tmp_path):
    source = tmp_path / "jobs.json"
    source.write_text(
        json.dumps(
            [
                {
                    "title": "Junior Backend Engineer",
                    "company": "Demo",
                    "location": "Zurich",
                    "description": "Requirements: Python and PostgreSQL.",
                    "source_id": "1",
                }
            ]
        ),
        encoding="utf-8",
    )
    engine = create_database_engine(Settings(database_url=f"sqlite:///{tmp_path / 'demo.db'}"))
    initialize_database(engine)
    event = ingest_ads(engine, FileImportCollector(source).collect(), "demo")
    with Session(engine) as session:
        job_id = session.scalar(select(Job.id))
    assert event.records_accepted == 1
    assert enrich_job(engine, job_id) == 2
    assert skill_frequency(engine)[0].required_count == 1
