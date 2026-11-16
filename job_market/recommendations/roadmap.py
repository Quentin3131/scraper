"""Dependency-aware learning sequence and evidence-linked project ideas."""

from dataclasses import dataclass

from job_market.recommendations.scoring import SkillRecommendation


@dataclass(frozen=True)
class RoadmapStep:
    day_range: str
    skill: str
    tier: str
    action: str


PROJECTS = (
    ("Production API", "Python, PostgreSQL, REST APIs, Docker", "Build, test, containerize, and document an API."),
    ("Full-stack dashboard", "TypeScript, React, SQL, REST APIs", "Build a filterable application with tests and deployment notes."),
    ("Cloud delivery pipeline", "Git, Docker, AWS, CI/CD", "Deploy a small service with repeatable build and release steps."),
)


def build_roadmap(recommendations: list[SkillRecommendation], weekly_hours: float) -> list[RoadmapStep]:
    hours = max(1.0, weekly_hours)
    steps = []
    for index, item in enumerate(recommendations[:6]):
        start = int(index * 30 / max(1, hours / 10)) + 1
        end = start + 29
        steps.append(
            RoadmapStep(
                day_range=f"{start}-{end}",
                skill=item.skill,
                tier=item.tier,
                action=f"Study {item.skill}, implement a small feature, and record evidence in a portfolio project.",
            )
        )
    return steps
