"""Configurable scoring model; scores are prioritization heuristics, not hiring odds."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from job_market.analysis.metrics import AnalysisScope, skill_frequency
from job_market.storage.models import Job, JobRequirement


@dataclass(frozen=True)
class UserProfile:
    target_role: str | None = None
    location: str | None = None
    weekly_learning_hours: float = 10
    skills: dict[str, str] | None = None


@dataclass(frozen=True)
class RecommendationWeights:
    demand: float = 0.45
    role_relevance: float = 0.25
    gap: float = 0.20
    effort: float = 0.10


@dataclass(frozen=True)
class SkillRecommendation:
    skill: str
    category: str
    score: float
    tier: str
    required_postings: int
    denominator: int
    proficiency: str
    rationale: str


@dataclass(frozen=True)
class JobMatch:
    job_id: int
    title: str
    company: str
    matched_skills: tuple[str, ...]
    missing_required_skills: tuple[str, ...]
    overlap_percentage: float


_PROFICIENCY = {"none": 0.0, "basic": 0.35, "intermediate": 0.7, "advanced": 1.0}


def recommendations(
    engine: Engine,
    profile: UserProfile,
    weights: RecommendationWeights = RecommendationWeights(),
) -> list[SkillRecommendation]:
    scope = AnalysisScope(
        roles=frozenset({profile.target_role}) if profile.target_role else None,
        location_contains=profile.location,
    )
    metrics = skill_frequency(engine, scope)
    skills = profile.skills or {}
    max_required = max((metric.required_count for metric in metrics), default=1)
    results = []
    for metric in metrics:
        proficiency = skills.get(metric.skill, "none").casefold()
        gap = 1 - _PROFICIENCY.get(proficiency, 0)
        demand = metric.required_count / max_required
        role_relevance = 1.0 if profile.target_role else 0.5
        effort_penalty = 0.0 if metric.category == "fundamentals" else 0.1
        score = 100 * (
            weights.demand * demand
            + weights.role_relevance * role_relevance
            + weights.gap * gap
            + weights.effort * (1 - effort_penalty)
        )
        tier = "Core" if metric.category == "fundamentals" else (
            "High-value specialization" if metric.required_percentage >= 25 else "Complementary"
        )
        results.append(
            SkillRecommendation(
                skill=metric.skill,
                category=metric.category,
                score=round(score, 2),
                tier=tier,
                required_postings=metric.required_count,
                denominator=metric.denominator,
                proficiency=proficiency,
                rationale=(
                    f"Required by {metric.required_count}/{metric.denominator} observed postings; "
                    f"your recorded proficiency is {proficiency}. This is a prioritization score, "
                    "not a hiring probability."
                ),
            )
        )
    return sorted(results, key=lambda item: (-item.score, item.skill))


def match_jobs(engine: Engine, profile: UserProfile) -> list[JobMatch]:
    known = {skill.casefold() for skill in (profile.skills or {})}
    with Session(engine) as session:
        jobs = list(session.scalars(select(Job).order_by(Job.id)))
        requirements = list(session.scalars(select(JobRequirement)))
    by_job: dict[int, list[JobRequirement]] = {}
    for requirement in requirements:
        by_job.setdefault(requirement.job_id, []).append(requirement)
    matches = []
    for job in jobs:
        if profile.target_role and job.role_category != profile.target_role:
            continue
        if profile.location and profile.location.casefold() not in (job.location or "").casefold():
            continue
        rows = by_job.get(job.id, [])
        required = {row.canonical_skill for row in rows if row.strength == "required"}
        matched = tuple(sorted(skill for skill in required if skill.casefold() in known))
        missing = tuple(sorted(required - set(matched)))
        overlap = len(matched) / len(required) * 100 if required else 0.0
        matches.append(JobMatch(job.id, job.title, job.company, matched, missing, round(overlap, 2)))
    return sorted(matches, key=lambda item: (-item.overlap_percentage, item.job_id))
