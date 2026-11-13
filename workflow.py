"""Coordinate local-LLM extraction and public profile search."""

from keyword_extractor import extract_search_criteria
from profile_search import search_profiles


def run_search(request: str) -> dict[str, object]:
    """Run the two-agent workflow for a free-form user request."""
    criteria = extract_search_criteria(request)
    outcome = search_profiles(criteria) if criteria.name.strip() else None
    return {"criteria": criteria, "outcome": outcome}