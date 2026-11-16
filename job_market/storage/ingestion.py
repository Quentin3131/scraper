"""Persist validated advertisements while retaining source-level auditability."""

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from job_market.collectors.base import CollectorError
from job_market.processing.cleaning import (
    clean_description,
    normalize_company,
    normalize_location,
    normalize_title,
)
from job_market.processing.deduplication import duplicate_key
from job_market.schemas import CollectionEvent, JobAdInput
from job_market.storage.models import CollectionRun, DuplicateRecord, Job, JobSource


def payload_hash(ad: JobAdInput) -> str:
    payload = json.dumps(ad.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ingest_ads(engine: Engine, ads: Iterable[JobAdInput], source: str) -> CollectionEvent:
    started_at = datetime.now(UTC)
    seen = accepted = 0
    with Session(engine) as session:
        run = CollectionRun(source=source, started_at=started_at, status="running")
        session.add(run)
        session.flush()
        run_id = run.id
        session.commit()
        try:
            for ad in ads:
                seen += 1
                accepted += _upsert_ad(session, ad, source)
            event = CollectionEvent(
                source=source,
                status="success",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                records_seen=seen,
                records_accepted=accepted,
            )
            run.status = event.status
            run.finished_at = event.finished_at
            run.records_seen = seen
            run.records_accepted = accepted
            session.commit()
            return event
        except (CollectorError, SQLAlchemyError) as error:
            session.rollback()
            with Session(engine) as failed_session:
                failed_run = failed_session.get(CollectionRun, run_id)
                if failed_run is not None:
                    failed_run.status = "failed"
                    failed_run.finished_at = datetime.now(UTC)
                    failed_run.records_seen = seen
                    failed_run.records_accepted = accepted
                    failed_run.error_message = str(error)
                    failed_session.commit()
            raise


def _upsert_ad(session: Session, ad: JobAdInput, source: str) -> int:
    retrieved_at = ad.collection_timestamp or datetime.now(UTC)
    cleaned = clean_description(ad.description)
    content_hash = payload_hash(ad)
    existing_source = None
    if ad.source_id:
        existing_source = session.scalar(
            select(JobSource).where(JobSource.source == source, JobSource.source_id == ad.source_id)
        )
    else:
        existing_source = session.scalar(
            select(JobSource).where(JobSource.source == source, JobSource.raw_payload_hash == content_hash)
        )
    if existing_source is not None:
        if existing_source.raw_payload_hash == content_hash:
            return 0
        job = existing_source.job
        existing_source.raw_payload_hash = content_hash
        existing_source.retrieved_at = retrieved_at
        existing_source.duplicate_decision = "updated"
        existing_source.duplicate_reason = "same source identifier with changed payload"
    else:
        key = duplicate_key(ad.title, ad.company, ad.location, cleaned)
        existing_job = session.scalar(
            select(Job).where(
                Job.normalized_title == normalize_title(ad.title),
                Job.normalized_company == normalize_company(ad.company),
                Job.normalized_location == normalize_location(ad.location),
                Job.cleaned_description == cleaned,
            )
        )
        if existing_job is not None:
            session.add(
                JobSource(
                    job_id=existing_job.id,
                    source=source,
                    source_id=ad.source_id,
                    source_url=str(ad.original_url) if ad.original_url else None,
                    retrieved_at=retrieved_at,
                    raw_payload_hash=content_hash,
                    duplicate_decision="duplicate",
                    duplicate_reason=f"cross-source exact normalized key: {key}",
                )
            )
            session.add(
                DuplicateRecord(
                    job_id=existing_job.id,
                    source=source,
                    source_id=ad.source_id,
                    decision="merged",
                    reason="normalized company, title, location, and cleaned description matched",
                    detected_at=retrieved_at,
                )
            )
            return 0
        job = Job(
            title=ad.title,
            normalized_title=normalize_title(ad.title),
            company=ad.company,
            normalized_company=normalize_company(ad.company),
            location=ad.location,
            normalized_location=normalize_location(ad.location),
            source=source,
            employment_type=ad.employment_type,
            work_arrangement=ad.work_arrangement,
            salary_text=ad.salary_text,
            original_url=str(ad.original_url) if ad.original_url else None,
            application_url=str(ad.application_url) if ad.application_url else None,
            publication_date=ad.publication_date,
            collection_timestamp=retrieved_at,
            raw_description=ad.description,
            cleaned_description=cleaned,
            content_hash=content_hash,
        )
        session.add(job)
        session.flush()
        session.add(
            JobSource(
                job_id=job.id,
                source=source,
                source_id=ad.source_id,
                source_url=str(ad.original_url) if ad.original_url else None,
                retrieved_at=retrieved_at,
                raw_payload_hash=content_hash,
                duplicate_decision="accepted",
                duplicate_reason="new source observation",
            )
        )
    job.title = ad.title
    job.normalized_title = normalize_title(ad.title)
    job.company = ad.company
    job.normalized_company = normalize_company(ad.company)
    job.location = ad.location
    job.normalized_location = normalize_location(ad.location)
    job.raw_description = ad.description
    job.cleaned_description = cleaned
    job.content_hash = content_hash
    return 1
