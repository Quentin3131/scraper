"""SQLAlchemy persistence model for auditable source observations and canonical jobs."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_accepted: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    normalized_title: Mapped[str] = mapped_column(String(300), index=True)
    company: Mapped[str] = mapped_column(String(300))
    normalized_company: Mapped[str] = mapped_column(String(300), index=True)
    location: Mapped[str | None] = mapped_column(String(300))
    normalized_location: Mapped[str | None] = mapped_column(String(300), index=True)
    source: Mapped[str] = mapped_column(String(100))
    employment_type: Mapped[str | None] = mapped_column(String(100))
    work_arrangement: Mapped[str | None] = mapped_column(String(100))
    salary_text: Mapped[str | None] = mapped_column(String(300))
    original_url: Mapped[str | None] = mapped_column(String(2000))
    application_url: Mapped[str | None] = mapped_column(String(2000))
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collection_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_description: Mapped[str] = mapped_column(Text)
    cleaned_description: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    seniority: Mapped[str | None] = mapped_column(String(40))
    role_category: Mapped[str | None] = mapped_column(String(40))
    classification_confidence: Mapped[float | None] = mapped_column(Float)
    classification_evidence: Mapped[list[str] | None] = mapped_column(JSON)

    sources: Mapped[list["JobSource"]] = relationship(back_populates="job")
    requirements: Mapped[list["JobRequirement"]] = relationship(back_populates="job")
    duplicate_records: Mapped[list["DuplicateRecord"]] = relationship(back_populates="job")


class JobSource(Base):
    __tablename__ = "job_sources"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_job_source_identifier"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    source: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str | None] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(String(2000))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_payload_hash: Mapped[str] = mapped_column(String(64))
    duplicate_decision: Mapped[str | None] = mapped_column(String(40))
    duplicate_reason: Mapped[str | None] = mapped_column(Text)

    job: Mapped[Job] = relationship(back_populates="sources")


class DuplicateRecord(Base):
    __tablename__ = "duplicate_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    source: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str | None] = mapped_column(String(300))
    decision: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    job: Mapped[Job] = relationship(back_populates="duplicate_records")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    canonical_skill: Mapped[str] = mapped_column(String(150), index=True)
    original_mention: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(80))
    strength: Mapped[str] = mapped_column(String(20))
    evidence_excerpt: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    extraction_method: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str | None] = mapped_column(String(100))

    job: Mapped[Job] = relationship(back_populates="requirements")
