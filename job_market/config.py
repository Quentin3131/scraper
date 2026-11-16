"""Application configuration with conservative, research-friendly defaults."""

import os
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

DEFAULT_SEARCH_TERMS = (
    "Junior Software Engineer",
    "Graduate Software Developer",
    "Entry Level Developer",
    "Junior Backend Developer",
    "Junior Frontend Developer",
    "Junior Full Stack Developer",
    "Associate Software Engineer",
    "Software Engineer I",
)


class Settings(BaseModel):
    database_url: str = "sqlite:///data/job_market.db"
    primary_location: str = "Zurich, Switzerland"
    secondary_locations: tuple[str, ...] = ("Switzerland",)
    languages: tuple[str, ...] = ("English", "German")
    seniority_levels: tuple[str, ...] = (
        "Internship",
        "Graduate",
        "Junior",
        "Entry Level",
        "Associate",
        "Software Engineer I",
    )
    search_terms: tuple[str, ...] = DEFAULT_SEARCH_TERMS
    recency_days: int = Field(default=30, ge=1, le=3650)
    sample_target: int = Field(default=500, ge=1, le=100_000)
    llm_enabled: bool = False

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("sqlite:///", "postgresql://", "postgresql+psycopg://")):
            raise ValueError("database_url must be a SQLite or PostgreSQL URL")
        return value

    @property
    def earliest_publication_date(self) -> date:
        return date.today() - timedelta(days=self.recency_days)

    @classmethod
    def from_environment(cls) -> "Settings":
        values: dict[str, object] = {}
        if database_url := os.getenv("JOB_MARKET_DATABASE_URL"):
            values["database_url"] = database_url
        if location := os.getenv("JOB_MARKET_PRIMARY_LOCATION"):
            values["primary_location"] = location
        if recency := os.getenv("JOB_MARKET_RECENCY_DAYS"):
            values["recency_days"] = int(recency)
        if target := os.getenv("JOB_MARKET_SAMPLE_TARGET"):
            values["sample_target"] = int(target)
        return cls(**values)

    def ensure_local_directories(self, project_root: Path = Path(".")) -> None:
        """Create only the local parent directory needed by a SQLite database."""
        if self.database_url.startswith("sqlite:///"):
            path = Path(self.database_url.removeprefix("sqlite:///"))
            if not path.is_absolute():
                path = project_root / path
            path.parent.mkdir(parents=True, exist_ok=True)
