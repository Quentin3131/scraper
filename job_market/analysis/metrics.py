"""Denominator-correct demand metrics over canonical, deduplicated jobs."""

from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from job_market.storage.models import Job, JobRequirement


@dataclass(frozen=True)
class AnalysisScope:
    seniorities: frozenset[str] | None = None
    roles: frozenset[str] | None = None
    location_contains: str | None = None
    include_ambiguous: bool = False


@dataclass(frozen=True)
class SkillMetric:
    skill: str
    category: str
    posting_count: int
    required_count: int
    preferred_count: int
    denominator: int
    posting_percentage: float
    required_percentage: float
    preferred_percentage: float


@dataclass(frozen=True)
class PairMetric:
    skill_a: str
    skill_b: str
    cooccurrence_count: int
    support: float
    confidence_a_to_b: float
    confidence_b_to_a: float
    lift: float


def eligible_jobs(session: Session, scope: AnalysisScope = AnalysisScope()) -> list[Job]:
    jobs = list(session.scalars(select(Job).order_by(Job.id)))
    result: list[Job] = []
    for job in jobs:
        if not scope.include_ambiguous and job.seniority == "ambiguous":
            continue
        if scope.seniorities and job.seniority not in scope.seniorities:
            continue
        if scope.roles and job.role_category not in scope.roles:
            continue
        if scope.location_contains and scope.location_contains.casefold() not in (job.location or "").casefold():
            continue
        result.append(job)
    return result


def skill_frequency(engine: Engine, scope: AnalysisScope = AnalysisScope()) -> list[SkillMetric]:
    with Session(engine) as session:
        jobs = eligible_jobs(session, scope)
        denominator = len(jobs)
        if denominator == 0:
            return []
        job_ids = [job.id for job in jobs]
        requirements = list(
            session.scalars(select(JobRequirement).where(JobRequirement.job_id.in_(job_ids)))
        )
    by_skill: dict[str, list[JobRequirement]] = {}
    for requirement in requirements:
        by_skill.setdefault(requirement.canonical_skill, []).append(requirement)
    metrics = []
    for skill, rows in by_skill.items():
        strengths_by_job: dict[int, set[str]] = {}
        for row in rows:
            strengths_by_job.setdefault(row.job_id, set()).add(row.strength)
        posting_count = len(strengths_by_job)
        required_count = sum("required" in values for values in strengths_by_job.values())
        preferred_count = sum("preferred" in values for values in strengths_by_job.values())
        category = rows[0].category
        metrics.append(
            SkillMetric(
                skill=skill,
                category=category,
                posting_count=posting_count,
                required_count=required_count,
                preferred_count=preferred_count,
                denominator=denominator,
                posting_percentage=posting_count / denominator * 100,
                required_percentage=required_count / denominator * 100,
                preferred_percentage=preferred_count / denominator * 100,
            )
        )
    return sorted(metrics, key=lambda metric: (-metric.required_count, -metric.posting_count, metric.skill))


def skill_cooccurrence(engine: Engine, scope: AnalysisScope = AnalysisScope()) -> list[PairMetric]:
    with Session(engine) as session:
        jobs = eligible_jobs(session, scope)
        rows = list(
            session.scalars(
                select(JobRequirement).where(JobRequirement.job_id.in_([job.id for job in jobs]))
            )
        )
    skills_by_job: dict[int, set[str]] = {}
    for row in rows:
        skills_by_job.setdefault(row.job_id, set()).add(row.canonical_skill)
    skill_counts = Counter(skill for skills in skills_by_job.values() for skill in skills)
    pair_counts = Counter(
        pair for skills in skills_by_job.values() for pair in combinations(sorted(skills), 2)
    )
    denominator = len(jobs)
    metrics = []
    for (skill_a, skill_b), count in pair_counts.items():
        if denominator == 0:
            continue
        metrics.append(
            PairMetric(
                skill_a=skill_a,
                skill_b=skill_b,
                cooccurrence_count=count,
                support=count / denominator,
                confidence_a_to_b=count / skill_counts[skill_a],
                confidence_b_to_a=count / skill_counts[skill_b],
                lift=(count * denominator) / (skill_counts[skill_a] * skill_counts[skill_b]),
            )
        )
    return sorted(metrics, key=lambda metric: (-metric.cooccurrence_count, metric.skill_a, metric.skill_b))
