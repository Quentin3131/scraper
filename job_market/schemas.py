"""Validated contracts shared by collectors, processing, storage, and analysis."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class RequirementStrength(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    MENTIONED = "mentioned"


class Seniority(StrEnum):
    INTERNSHIP = "internship"
    GRADUATE = "graduate"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    AMBIGUOUS = "ambiguous"


class RoleCategory(StrEnum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULL_STACK = "full_stack"
    GENERAL = "general"
    PLATFORM_DEVOPS = "platform_devops"
    QA_SDET = "qa_sdet"
    OTHER = "other"


class JobAdInput(BaseModel):
    """Source-neutral advertisement payload; absent source fields stay absent."""

    model_config = ConfigDict(extra="allow")

    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    description: str = Field(min_length=1)
    location: str | None = None
    source: str = Field(min_length=1)
    original_url: HttpUrl | None = None
    application_url: HttpUrl | None = None
    source_id: str | None = None
    publication_date: datetime | None = None
    collection_timestamp: datetime | None = None
    employment_type: str | None = None
    work_arrangement: str | None = None
    salary_text: str | None = None

    @field_validator("title", "company", "description", "source")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value


class SkillRequirement(BaseModel):
    canonical_skill: str = Field(min_length=1)
    original_mention: str = Field(min_length=1)
    category: str = Field(min_length=1)
    strength: RequirementStrength
    evidence_excerpt: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    extraction_method: str = Field(min_length=1)
    model_version: str | None = None


class ClassificationEvidence(BaseModel):
    label: Seniority | RoleCategory
    confidence: float = Field(ge=0, le=1)
    excerpts: list[str] = Field(default_factory=list)


class CollectionEvent(BaseModel):
    source: str = Field(min_length=1)
    status: str = Field(pattern=r"^(success|failed|skipped)$")
    started_at: datetime
    finished_at: datetime | None = None
    records_seen: int = Field(default=0, ge=0)
    records_accepted: int = Field(default=0, ge=0)
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
