# Job Market Intelligence

Local-first tooling for collecting permitted job advertisements and producing
auditable entry-level software engineering market analysis.

## Phase 2 usage

Install the package and development tools:

```bash
python3 -m pip install -e '.[dev]'
```

Initialize a local SQLite database:

```bash
job-market --database-url sqlite:///data/job_market.db
```

Import an authorized CSV or JSON export:

```bash
job-market import data/jobs.json \
  --source authorized_export \
  --database-url sqlite:///data/job_market.db
```

Input records require `title`, `company`, and `description`. Optional fields
include `source_id`, `location`, `original_url`, `application_url`,
`publication_date`, `collection_timestamp`, `employment_type`,
`work_arrangement`, and `salary_text`. JSON accepts either a list of records or
an object containing a `jobs` list. Imported records retain raw descriptions,
source attribution, retrieval timestamps, payload hashes, and collection-run
status. Re-importing an unchanged `source_id` (or unchanged payload without
one) is idempotent.

Descriptions are cleaned into a separate field while originals remain intact.
Cross-source records are merged only when normalized company, title, location,
and cleaned description all match; every merge is recorded in the duplicate
audit table.

Enrich a persisted job with deterministic skill and classification analysis:

```bash
job-market enrich --job-id 1 --database-url sqlite:///data/job_market.db
```

Extraction records canonical skill names, original mentions, requirement
strength, evidence excerpts, confidence, extraction method, and taxonomy
version. Seniority classification uses explicit experience and eligibility
evidence, so a junior title with a five-year requirement is classified as
senior rather than trusted from its title alone. The optional LLM boundary
validates structured provider output but does not require network access or an
API key.

Generate denominator-correct skill demand and co-occurrence metrics:

```bash
job-market analyze --database-url sqlite:///data/job_market.db --export data/report.json
```

Reports include unique eligible-posting denominators, required/preferred
counts and percentages, pairwise support/confidence/lift, and retain the
posting-level evidence in the database. Use the analysis modules directly for
role, seniority, or location scopes.

Run the local dashboard after installing its optional dependencies:

```bash
python3 -m pip install -e '.[dashboard]'
streamlit run job_market/dashboard/main.py
```

The dashboard provides overview metrics, filtered skill demand, technology
combinations, job evidence, data-quality reporting, and CSV downloads. It
reads the same SQLite database as the CLI and does not collect data itself.

The Learning Roadmap view accepts a target role, location, weekly study time,
and current proficiency entries. It reports transparent skill overlap and
missing required skills for observed jobs; these are not hiring probabilities.

Only sources that the user is authorized to access should be imported. This
project does not scrape LinkedIn, automate login, bypass CAPTCHAs, or evade
source access controls.

Run checks with:

```bash
python3 -m pytest
python3 -m ruff check job_market tests
```

## Reproducible demo and validation

The checked-in `data/demo_jobs.json` file is labeled sample data, not observed
market evidence. Run the complete local pipeline with:

```bash
python3 scripts/run_demo.py
python3 scripts/evaluate_fixtures.py
```

The evaluation fixture currently contains three manually labeled examples.
Its output is a measurement of this fixture only; it must not be generalized
to the broader job market. For the planned 100-description evaluation, add
diverse reviewed labels to `data/evaluation_labels.json` and report precision,
recall, F1, seniority accuracy, and sample size.

Build and run the dashboard in Docker:

```bash
docker build -t job-market-intelligence .
docker run --rm -p 8501:8501 -v "$PWD/data:/app/data" job-market-intelligence
```

## Limitations and compliance

This application does not scrape LinkedIn, automate authentication, bypass
CAPTCHAs, evade rate limits, or use undocumented endpoints. LinkedIn data is
supported only through authorized user-provided exports or URLs. Public
employer pages and third-party feeds require independent permission checks
before an adapter is configured.

Observed postings are a sample shaped by source coverage, search terms,
language, geography, publication timing, duplicate rules, missing fields, and
classification uncertainty. Percentages always show their eligible-posting
denominator, and recommendations are explainable prioritization heuristics,
not hiring probabilities or guarantees. Missing values are retained as
missing; no jobs or measurements are fabricated.
