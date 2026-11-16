"""Deterministic, evidence-preserving skill extraction."""

import re

from job_market.schemas import RequirementStrength, SkillRequirement
from job_market.taxonomy import SKILLS, TAXONOMY_VERSION

_PREFERRED_RE = re.compile(
    r"\b(?:nice to have|preferred|bonus|plus|ideally|would be an advantage|desirable)\b",
    re.IGNORECASE,
)
_REQUIRED_RE = re.compile(
    r"\b(?:required|must have|must[- ]have|essential|qualifications|requirements)\b",
    re.IGNORECASE,
)


def extract_skills(text: str) -> list[SkillRequirement]:
    """Extract known taxonomy entries using token boundaries and local evidence."""
    results: list[SkillRequirement] = []
    lowered = text.casefold()
    for canonical, metadata in SKILLS.items():
        aliases = metadata["aliases"]
        matches = [
            match
            for alias in aliases
            for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", lowered)
        ]
        if not matches:
            continue
        match = min(matches, key=lambda item: item.start())
        start = max(0, match.start() - 140)
        end = min(len(text), match.end() + 140)
        excerpt = " ".join(text[start:end].split())
        sentence_start = max(
            lowered.rfind(".", 0, match.start()),
            lowered.rfind("!", 0, match.start()),
            lowered.rfind("?", 0, match.start()),
            lowered.rfind("\n", 0, match.start()),
        )
        sentence_end_candidates = [
            position
            for position in (
                lowered.find(".", match.end()),
                lowered.find("!", match.end()),
                lowered.find("?", match.end()),
                lowered.find("\n", match.end()),
            )
            if position >= 0
        ]
        context = lowered[
            sentence_start + 1 : min(sentence_end_candidates, default=len(lowered)) + 1
        ]
        if _PREFERRED_RE.search(context) and not _REQUIRED_RE.search(context):
            strength = RequirementStrength.PREFERRED
        elif _REQUIRED_RE.search(context):
            strength = RequirementStrength.REQUIRED
        else:
            strength = RequirementStrength.MENTIONED
        results.append(
            SkillRequirement(
                canonical_skill=canonical,
                original_mention=text[match.start() : match.end()],
                category=str(metadata["category"]),
                strength=strength,
                evidence_excerpt=excerpt,
                confidence=0.98 if len(matches) == 1 else 0.9,
                extraction_method="taxonomy_rules",
                model_version=TAXONOMY_VERSION,
            )
        )
    return results
