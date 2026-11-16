"""Database engine and schema bootstrap."""

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from job_market.config import Settings
from job_market.storage.models import Base


def create_database_engine(settings: Settings) -> Engine:
    settings.ensure_local_directories(Path.cwd())
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args, future=True)


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name == "sqlite":
        _upgrade_sqlite_schema(engine)


def _upgrade_sqlite_schema(engine: Engine) -> None:
    """Apply additive MVP migrations for databases created by earlier phases."""
    existing_names = {column["name"] for column in inspect(engine).get_columns("jobs")}
    additions = {
        "normalized_title": "VARCHAR(300) NOT NULL DEFAULT ''",
        "normalized_company": "VARCHAR(300) NOT NULL DEFAULT ''",
        "normalized_location": "VARCHAR(300)",
        "employment_type": "VARCHAR(100)",
        "work_arrangement": "VARCHAR(100)",
        "salary_text": "VARCHAR(300)",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing_names:
                connection.execute(text(f"ALTER TABLE jobs ADD COLUMN {name} {definition}"))
