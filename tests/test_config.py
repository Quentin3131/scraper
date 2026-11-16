from datetime import date

import pytest
from pydantic import ValidationError

from job_market.config import Settings


def test_defaults_target_zurich_and_recent_postings():
    settings = Settings()
    assert settings.primary_location == "Zurich, Switzerland"
    assert settings.recency_days == 30
    assert settings.earliest_publication_date <= date.today()
    assert "Software Engineer I" in settings.search_terms


def test_invalid_database_scheme_is_rejected():
    with pytest.raises(ValidationError):
        Settings(database_url="file://not-supported")
