from sqlalchemy import inspect

from job_market.config import Settings
from job_market.storage.database import create_database_engine, initialize_database


def test_initialize_database_creates_auditable_tables(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}")
    engine = create_database_engine(settings)
    initialize_database(engine)
    tables = set(inspect(engine).get_table_names())
    assert {"jobs", "job_sources", "job_requirements"} <= tables
