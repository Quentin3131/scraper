from job_market.processing.cleaning import clean_description, normalize_company, normalize_title


def test_cleaning_removes_html_and_navigation_but_preserves_requirements():
    text = "<p>Apply now</p>\r\n<b>Requirements:</b> Python   and SQL"
    assert clean_description(text) == "Requirements: Python and SQL"


def test_normalization_handles_case_and_company_suffixes():
    assert normalize_title(" Junior Software Engineer ") == "junior software engineer"
    assert normalize_company("Acme GmbH") == "acme"
