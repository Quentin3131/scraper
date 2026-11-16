import json

from job_market.collectors.file_import import FileImportCollector


def test_json_import_validates_and_assigns_source(tmp_path):
    path = tmp_path / "jobs.json"
    path.write_text(
        json.dumps(
            [
                {"title": "Junior Engineer", "company": "Acme", "description": "Python", "source_id": "1"}
            ]
        ),
        encoding="utf-8",
    )
    jobs = list(FileImportCollector(path, source_name="authorized_export").collect())
    assert len(jobs) == 1
    assert jobs[0].source == "authorized_export"


def test_csv_import_supports_utf8_bom(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text(
        "title,company,description\nJunior Engineer,Acme,Python\n",
        encoding="utf-8-sig",
    )
    assert next(iter(FileImportCollector(path).collect())).company == "Acme"
