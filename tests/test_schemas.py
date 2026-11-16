import pytest
from pydantic import ValidationError

from job_market.schemas import JobAdInput, RequirementStrength, SkillRequirement


def test_job_ad_requires_non_blank_core_fields():
    with pytest.raises(ValidationError):
        JobAdInput(title=" ", company="Acme", description="text", source="import")


def test_skill_requirement_preserves_auditable_evidence():
    requirement = SkillRequirement(
        canonical_skill="PostgreSQL",
        original_mention="Postgres",
        category="database",
        strength=RequirementStrength.REQUIRED,
        evidence_excerpt="Experience with Postgres is required.",
        confidence=0.98,
        extraction_method="taxonomy",
    )
    assert requirement.canonical_skill == "PostgreSQL"
    assert requirement.strength == RequirementStrength.REQUIRED
