"""Conservative, explainable duplicate keys for cross-source observations."""

import hashlib

from job_market.processing.cleaning import normalize_company, normalize_location, normalize_title


def duplicate_key(title: str, company: str, location: str | None, description: str) -> str:
    """Require matching normalized identity and content before automatic merging."""
    identity = "|".join(
        (normalize_company(company), normalize_title(title), normalize_location(location))
    )
    content = hashlib.sha256(description.encode("utf-8")).hexdigest()
    return f"{identity}|{content}"
