from sqlalchemy.orm import Session

from job_market.config import Settings
from job_market.schemas import JobAdInput
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.ingestion import ingest_ads
from job_market.storage.models import CollectionRun, DuplicateRecord, Job, JobSource


def test_ingestion_is_incremental_for_unchanged_source_identifier(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}")
    engine = create_database_engine(settings)
    initialize_database(engine)
    ad = JobAdInput(title="Junior Engineer", company="Acme", description="Python", source="export", source_id="1")
    first = ingest_ads(engine, [ad], "export")
    second = ingest_ads(engine, [ad], "export")
    with Session(engine) as session:
        assert first.records_accepted == 1
        assert second.records_accepted == 0
        assert session.query(Job).count() == 1
        assert session.query(JobSource).count() == 1
        assert session.query(CollectionRun).count() == 2


def test_cross_source_exact_duplicate_is_merged_and_audited(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'jobs.db'}")
    engine = create_database_engine(settings)
    initialize_database(engine)
    first = JobAdInput(
        title="Junior Engineer", company="Acme GmbH", location="Zurich",
        description="<p>Python and SQL</p>", source="board_a", source_id="a",
    )
    second = first.model_copy(update={"source": "board_b", "source_id": "b"})
    assert ingest_ads(engine, [first], "board_a").records_accepted == 1
    assert ingest_ads(engine, [second], "board_b").records_accepted == 0
    with Session(engine) as session:
        assert session.query(Job).count() == 1
        assert session.query(JobSource).count() == 2
        assert session.query(DuplicateRecord).count() == 1
