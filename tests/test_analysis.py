import json

from sqlalchemy.orm import Session

from job_market.analysis.export import export_rows
from job_market.analysis.metrics import AnalysisScope, skill_cooccurrence, skill_frequency
from job_market.config import Settings
from job_market.processing.enrichment import enrich_job
from job_market.schemas import JobAdInput
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import Job


def build_analysis_db(tmp_path):
    engine = create_database_engine(Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}"))
    initialize_database(engine)
    ads = [
        JobAdInput(
            title="Junior Backend Engineer", company="Acme", location="Zurich",
            description="Requirements: Python and PostgreSQL. Docker is a plus.",
            source="import", source_id="1",
        ),
        JobAdInput(
            title="Junior Frontend Engineer", company="Beta", location="Zurich",
            description="Requirements: JavaScript and React.",
            source="import", source_id="2",
        ),
    ]
    ingest_ads(engine, ads, "import")
    with Session(engine) as session:
        ids = [job.id for job in session.query(Job).all()]
    for job_id in ids:
        enrich_job(engine, job_id)
    return engine


def test_frequency_uses_unique_eligible_postings_denominator(tmp_path):
    metrics = skill_frequency(build_analysis_db(tmp_path), AnalysisScope(seniorities=frozenset({"junior"})))
    python = next(metric for metric in metrics if metric.skill == "Python")
    assert python.denominator == 2
    assert python.required_count == 1
    assert python.required_percentage == 50


def test_cooccurrence_reports_support_confidence_and_lift(tmp_path):
    pairs = skill_cooccurrence(build_analysis_db(tmp_path))
    pair = next(item for item in pairs if {item.skill_a, item.skill_b} == {"Python", "PostgreSQL"})
    assert pair.cooccurrence_count == 1
    assert pair.support == 0.5
    assert pair.lift == 2


def test_export_writes_json_and_csv(tmp_path):
    rows = [{"skill": "Python", "required_count": 2}]
    json_path, csv_path = tmp_path / "report.json", tmp_path / "report.csv"
    export_rows(rows, json_path)
    export_rows(rows, csv_path)
    assert json.loads(json_path.read_text()) == rows
    assert "skill" in csv_path.read_text()
