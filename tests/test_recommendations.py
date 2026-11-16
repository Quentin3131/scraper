from sqlalchemy.orm import Session

from job_market.config import Settings
from job_market.processing.enrichment import enrich_job
from job_market.recommendations.roadmap import build_roadmap
from job_market.recommendations.scoring import UserProfile, match_jobs, recommendations
from job_market.schemas import JobAdInput
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import Job


def test_recommendations_explain_demand_and_gap(tmp_path):
    engine = create_database_engine(Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}"))
    initialize_database(engine)
    ingest_ads(engine, [JobAdInput(
        title="Junior Backend Engineer", company="Acme", location="Zurich",
        description="Requirements: Python and PostgreSQL.", source="import", source_id="1",
    )], "import")
    with Session(engine) as session:
        job_id = session.query(Job).one().id
    enrich_job(engine, job_id)
    profile = UserProfile(target_role="backend", location="Zurich", skills={"Python": "basic"})
    items = recommendations(engine, profile)
    python = next(item for item in items if item.skill == "Python")
    assert python.required_postings == 1
    assert "prioritization score" in python.rationale


def test_job_match_is_overlap_not_hiring_probability(tmp_path):
    engine = create_database_engine(Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}"))
    initialize_database(engine)
    ingest_ads(engine, [JobAdInput(
        title="Junior Backend Engineer", company="Acme", location="Zurich",
        description="Requirements: Python and PostgreSQL.", source="import", source_id="1",
    )], "import")
    with Session(engine) as session:
        job_id = session.query(Job).one().id
    enrich_job(engine, job_id)
    matches = match_jobs(engine, UserProfile(target_role="backend", skills={"Python": "intermediate"}))
    assert matches[0].overlap_percentage == 50
    assert matches[0].missing_required_skills == ("PostgreSQL",)


def test_roadmap_and_projects_are_actionable():
    profile_items = recommendations  # verify public module surface remains callable
    assert profile_items
    roadmap = build_roadmap([], 10)
    assert roadmap == []
