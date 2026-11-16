"""Interactive local dashboard for auditable market analysis."""

import os
from dataclasses import asdict

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from job_market.analysis.metrics import AnalysisScope, skill_cooccurrence, skill_frequency
from job_market.analysis.quality import data_quality_report
from job_market.config import Settings
from job_market.recommendations.roadmap import PROJECTS, build_roadmap
from job_market.recommendations.scoring import UserProfile, match_jobs, recommendations
from job_market.storage.database import create_database_engine, initialize_database
from job_market.storage.models import Job, JobRequirement


@st.cache_resource
def get_engine(database_url: str):
    settings = Settings(database_url=database_url)
    engine = create_database_engine(settings)
    initialize_database(engine)
    return engine


def load_jobs(engine) -> list[dict[str, object]]:
    with Session(engine) as session:
        jobs = list(session.scalars(select(Job).order_by(Job.id.desc())))
        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location or "",
                "source": job.source,
                "seniority": job.seniority or "unclassified",
                "role_category": job.role_category or "unclassified",
                "publication_date": job.publication_date,
                "original_url": job.original_url or "",
                "application_url": job.application_url or "",
                "description": job.raw_description,
            }
            for job in jobs
        ]


def job_requirements(engine, job_id: int) -> list[dict[str, object]]:
    with Session(engine) as session:
        rows = list(
            session.scalars(
                select(JobRequirement)
                .where(JobRequirement.job_id == job_id)
                .order_by(JobRequirement.canonical_skill)
            )
        )
        return [
            {
                "skill": row.canonical_skill,
                "strength": row.strength,
                "category": row.category,
                "evidence": row.evidence_excerpt,
            }
            for row in rows
        ]


def main() -> None:
    st.set_page_config(page_title="Job Market Intelligence", layout="wide")
    st.title("Entry-Level Software Engineering Market Intelligence")
    st.caption("Observed postings are evidence, not the entire job market or a hiring probability.")

    default_url = os.getenv("JOB_MARKET_DATABASE_URL", "sqlite:///data/job_market.db")
    database_url = st.sidebar.text_input("Database URL", value=default_url)
    try:
        engine = get_engine(database_url)
        jobs = load_jobs(engine)
    except (OSError, SQLAlchemyError, ValueError) as error:
        st.error(f"Could not open database: {error}")
        st.stop()

    frame = pd.DataFrame(jobs)
    roles = sorted(value for value in frame["role_category"].dropna().unique()) if not frame.empty else []
    seniorities = (
        sorted(value for value in frame["seniority"].dropna().unique()) if not frame.empty else []
    )
    selected_roles = st.sidebar.multiselect("Role", roles)
    selected_seniorities = st.sidebar.multiselect("Seniority", seniorities)
    location = st.sidebar.text_input("Location contains")
    scope = AnalysisScope(
        roles=frozenset(selected_roles) or None,
        seniorities=frozenset(selected_seniorities) or None,
        location_contains=location or None,
    )

    tabs = st.tabs(
        [
            "Overview",
            "Skill Demand",
            "Technology Combinations",
            "Job Explorer",
            "Learning Roadmap",
            "Data Quality",
        ]
    )
    with tabs[0]:
        show_overview(frame, engine, scope)
    with tabs[1]:
        show_skill_demand(engine, scope)
    with tabs[2]:
        show_combinations(engine, scope)
    with tabs[3]:
        show_job_explorer(engine, frame)
    with tabs[4]:
        show_roadmap(engine, scope)
    with tabs[5]:
        show_quality(engine)


def show_overview(frame: pd.DataFrame, engine, scope: AnalysisScope) -> None:
    metrics = skill_frequency(engine, scope)
    columns = st.columns(4)
    columns[0].metric("Unique postings", len(frame))
    columns[1].metric("Companies", frame["company"].nunique() if not frame.empty else 0)
    columns[2].metric("Observed sources", frame["source"].nunique() if not frame.empty else 0)
    columns[3].metric("Skills extracted", len(metrics))
    if metrics:
        st.subheader("Most requested skills")
        st.dataframe(pd.DataFrame([asdict(item) for item in metrics[:10]]), hide_index=True)


def show_skill_demand(engine, scope: AnalysisScope) -> None:
    metrics = skill_frequency(engine, scope)
    if not metrics:
        st.info("No enriched postings match the selected filters.")
        return
    frame = pd.DataFrame([asdict(item) for item in metrics])
    st.download_button(
        "Download skill demand CSV",
        frame.to_csv(index=False),
        "skill-demand.csv",
        "text/csv",
    )
    st.bar_chart(frame.set_index("skill")[["required_count", "preferred_count"]].head(20))
    st.dataframe(frame, hide_index=True)


def show_combinations(engine, scope: AnalysisScope) -> None:
    pairs = skill_cooccurrence(engine, scope)
    if not pairs:
        st.info("No skill combinations are available for the selected filters.")
        return
    frame = pd.DataFrame([asdict(item) for item in pairs])
    st.download_button(
        "Download combinations CSV",
        frame.to_csv(index=False),
        "skill-combinations.csv",
        "text/csv",
    )
    st.dataframe(frame.head(50), hide_index=True)


def show_job_explorer(engine, frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No postings have been imported.")
        return
    query = st.text_input("Search title, company, location, or description")
    if query:
        mask = frame.astype(str).apply(
            lambda column: column.str.contains(query, case=False, na=False, regex=False)
        ).any(axis=1)
        frame = frame[mask]
    st.download_button("Download job records CSV", frame.to_csv(index=False), "jobs.csv", "text/csv")
    st.dataframe(frame.drop(columns=["description"]), hide_index=True, use_container_width=True)
    if not frame.empty:
        selected_id = st.selectbox("Show evidence for job", frame["id"].tolist())
        selected = frame[frame["id"] == selected_id].iloc[0]
        st.markdown(f"### {selected['title']} — {selected['company']}")
        st.write(selected["description"])
        requirements = job_requirements(engine, int(selected_id))
        if requirements:
            st.dataframe(pd.DataFrame(requirements), hide_index=True)


def show_quality(engine) -> None:
    report = data_quality_report(engine)
    st.json(report)


def show_roadmap(engine, scope: AnalysisScope) -> None:
    st.subheader("Personal learning roadmap")
    target_role = st.selectbox("Target role", [""] + sorted(scope.roles or {"backend", "frontend", "full_stack", "general"}))
    location = st.text_input("Profile location", value=scope.location_contains or "")
    weekly_hours = st.number_input("Weekly learning hours", min_value=1.0, max_value=80.0, value=10.0)
    raw_skills = st.text_area("Current skills (one `Skill=proficiency` per line)", "Python=basic\nGit=intermediate")
    skills = {}
    for line in raw_skills.splitlines():
        if "=" in line:
            skill, proficiency = line.split("=", 1)
            skills[skill.strip()] = proficiency.strip()
    profile = UserProfile(target_role=target_role or None, location=location or None, weekly_learning_hours=weekly_hours, skills=skills)
    ranked = recommendations(engine, profile)
    if ranked:
        st.dataframe(pd.DataFrame([asdict(item) for item in ranked]), hide_index=True)
        st.subheader("30/60/90-day sequence")
        st.dataframe(pd.DataFrame([asdict(item) for item in build_roadmap(ranked, weekly_hours)]), hide_index=True)
    st.subheader("Portfolio project concepts")
    st.dataframe(pd.DataFrame(PROJECTS, columns=["project", "skills", "demonstration"]), hide_index=True)
    st.subheader("Observed job overlap")
    matches = match_jobs(engine, profile)
    if matches:
        st.dataframe(pd.DataFrame([asdict(item) for item in matches]), hide_index=True)


if __name__ == "__main__":
    main()
