"""Apply extraction and classification to persisted canonical jobs."""

from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from job_market.processing.classification import classify_role, classify_seniority
from job_market.processing.skill_extraction import extract_skills
from job_market.storage.models import Job, JobRequirement


def enrich_job(engine: Engine, job_id: int) -> int:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError(f"job {job_id} does not exist")
        text = job.cleaned_description or job.raw_description
        seniority, seniority_confidence, seniority_evidence = classify_seniority(job.title, text)
        role, role_confidence, role_evidence = classify_role(job.title, text)
        job.seniority = seniority.value
        job.role_category = role.value
        job.classification_confidence = min(seniority_confidence, role_confidence)
        job.classification_evidence = seniority_evidence + role_evidence
        session.execute(delete(JobRequirement).where(JobRequirement.job_id == job_id))
        requirements = extract_skills(text)
        for requirement in requirements:
            session.add(JobRequirement(job_id=job_id, **requirement.model_dump()))
        session.commit()
        return len(requirements)
