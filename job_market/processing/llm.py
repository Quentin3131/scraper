"""Optional structured extraction boundary; no provider or network dependency in the MVP."""

from collections.abc import Callable

from job_market.schemas import SkillRequirement


class LLMExtractionError(RuntimeError):
    """Raised when an external structured extraction provider returns invalid data."""


def validate_llm_requirements(
    payload: list[dict[str, object]],
    validator: Callable[[dict[str, object]], SkillRequirement] = SkillRequirement.model_validate,
) -> list[SkillRequirement]:
    """Validate provider output before it can enter the evidence store."""
    try:
        return [validator(item) for item in payload]
    except Exception as error:
        raise LLMExtractionError(f"invalid structured extraction response: {error}") from error
