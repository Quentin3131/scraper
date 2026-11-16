from sqlalchemy.orm import Session

from job_market.config import Settings
from job_market.processing.classification import classify_role, classify_seniority
from job_market.processing.enrichment import enrich_job
from job_market.processing.llm import LLMExtractionError, validate_llm_requirements
from job_market.processing.skill_extraction import extract_skills
from job_market.schemas import JobAdInput, RequirementStrength
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import Job, JobRequirement


def test_extraction_normalizes_alias_and_strength_with_evidence():
    results = extract_skills("Requirements: experience with Postgres. AWS is a plus.")
    by_name = {item.canonical_skill: item for item in results}
    assert by_name["PostgreSQL"].strength == RequirementStrength.REQUIRED
    assert by_name["AWS"].strength == RequirementStrength.PREFERRED
    assert "Postgres" in by_name["PostgreSQL"].evidence_excerpt


def test_extraction_avoids_javascript_substring_false_positive_for_java():
    assert {item.canonical_skill for item in extract_skills("Build with JavaScript")} == {"JavaScript"}


def test_classifiers_report_misleading_junior_title():
    seniority, _, evidence = classify_seniority("Junior Developer", "At least 5 years of experience required.")
    assert seniority.value == "senior"
    assert "5 years" in evidence[0]
    role, _, _ = classify_role("Full Stack Engineer", "React frontend and Python backend")
    assert role.value == "full_stack"


def test_enrichment_persists_requirements_and_classification(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}")
    engine = create_database_engine(settings)
    initialize_database(engine)
    ad = JobAdInput(
        title="Junior Backend Engineer", company="Acme", description="Requirements: Python and PostgreSQL.",
        source="import", source_id="1",
    )
    ingest_ads(engine, [ad], "import")
    with Session(engine) as session:
        job_id = session.query(Job).one().id
    assert enrich_job(engine, job_id) == 2
    with Session(engine) as session:
        job = session.get(Job, job_id)
        assert job.seniority == "junior"
        assert session.query(JobRequirement).count() == 2


def test_llm_boundary_rejects_invalid_structured_output():
    try:
        validate_llm_requirements([{"canonical_skill": "Python"}])
    except LLMExtractionError:
        pass
    else:
        raise AssertionError("invalid output must be rejected")
