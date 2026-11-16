from job_market.evaluation import LabeledPosting, evaluate


def test_evaluation_reports_reproducible_skill_and_seniority_metrics():
    result = evaluate(
        [
            LabeledPosting(
                title="Junior Backend Engineer",
                description="Requirements: Python and PostgreSQL.",
                expected_skills=frozenset({"Python", "PostgreSQL"}),
                expected_seniority="junior",
            )
        ]
    )
    assert result.sample_size == 1
    assert result.skill_f1 == 1
    assert result.seniority_accuracy == 1
