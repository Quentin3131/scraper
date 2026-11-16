"""Explainable seniority and role classification using title and description evidence."""

import re

from job_market.schemas import RoleCategory, Seniority


def classify_seniority(title: str, description: str) -> tuple[Seniority, float, list[str]]:
    text = f"{title}\n{description}"
    lowered = text.casefold()
    evidence: list[str] = []
    years = [int(value) for value in re.findall(r"(?<!\d)(\d{1,2})\+?\s+years?", lowered)]
    if "intern" in lowered or "internship" in lowered:
        evidence.append("internship terminology")
        return Seniority.INTERNSHIP, 0.95, evidence
    if any(term in lowered for term in ("new grad", "graduate", "recent graduate")):
        evidence.append("graduate terminology")
        return Seniority.GRADUATE, 0.92, evidence
    if years and max(years) >= 5:
        evidence.append(f"explicit requirement of {max(years)} years")
        return Seniority.SENIOR, 0.96, evidence
    if years and max(years) >= 3:
        evidence.append(f"explicit requirement of {max(years)} years")
        return Seniority.MID, 0.9, evidence
    if any(term in lowered for term in ("junior", "entry level", "associate", "software engineer i")):
        evidence.append("entry-level title terminology")
        return Seniority.JUNIOR, 0.88, evidence
    if years and max(years) <= 2:
        evidence.append(f"explicit requirement of {max(years)} years")
        return Seniority.JUNIOR, 0.82, evidence
    return Seniority.AMBIGUOUS, 0.45, evidence


def classify_role(title: str, description: str) -> tuple[RoleCategory, float, list[str]]:
    lowered = f"{title}\n{description}".casefold()
    evidence: list[str] = []
    if "qa" in lowered or "sdet" in lowered or "test automation" in lowered:
        evidence.append("QA/SDET terminology")
        return RoleCategory.QA_SDET, 0.9, evidence
    if any(term in lowered for term in ("devops", "platform engineer", "site reliability", "kubernetes")):
        evidence.append("platform/DevOps terminology")
        return RoleCategory.PLATFORM_DEVOPS, 0.86, evidence
    frontend = any(term in lowered for term in ("frontend", "front-end", "react", "angular", "vue"))
    backend = any(term in lowered for term in ("backend", "back-end", "spring", "django", "fastapi", "node.js"))
    if frontend and backend:
        evidence.append("frontend and backend terminology")
        return RoleCategory.FULL_STACK, 0.9, evidence
    if frontend:
        evidence.append("frontend terminology")
        return RoleCategory.FRONTEND, 0.84, evidence
    if backend:
        evidence.append("backend terminology")
        return RoleCategory.BACKEND, 0.84, evidence
    return RoleCategory.GENERAL, 0.5, evidence
