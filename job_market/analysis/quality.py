"""Collection and extraction quality indicators shown alongside market claims."""

from dataclasses import asdict

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from job_market.storage.models import CollectionRun, DuplicateRecord, Job, JobRequirement, JobSource


def data_quality_report(engine: Engine) -> dict[str, object]:
    with Session(engine) as session:
        jobs = list(session.scalars(select(Job)))
        source_counts = dict(
            session.execute(select(JobSource.source, func.count()).group_by(JobSource.source)).all()
        )
        return {
            "canonical_postings": len(jobs),
            "companies": len({job.normalized_company for job in jobs}),
            "source_observations": session.query(JobSource).count(),
            "duplicates_merged": session.query(DuplicateRecord).count(),
            "missing_descriptions": sum(not bool(job.raw_description.strip()) for job in jobs),
            "missing_locations": sum(not bool(job.location) for job in jobs),
            "unclassified_jobs": sum(not job.seniority for job in jobs),
            "requirements_extracted": session.query(JobRequirement).count(),
            "collection_runs": session.query(CollectionRun).count(),
            "source_breakdown": source_counts,
        }


def as_dicts(items: list[object]) -> list[dict[str, object]]:
    return [asdict(item) for item in items]
