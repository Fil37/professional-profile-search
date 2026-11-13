"""DDGS search for publicly indexed LinkedIn profile pages."""

import json

from ddgs import DDGS
from langchain_core.tools import tool

from config import SEARCH_MAX_RESULTS
from schemas import SearchResult


def search_ddgs_profiles(query: str) -> list[SearchResult]:
    """Return public LinkedIn profile results from DDGS."""
    search_query = f"site:linkedin.com/in/ {query}"
    try:
        with DDGS() as search_engine:
            results = search_engine.text(
                search_query,
                region="wt-wt",
                max_results=SEARCH_MAX_RESULTS,
            )
    except Exception as error:
        raise RuntimeError(f"DDGS search failed: {error}") from error

    return [
        SearchResult(
            title=result.get("title", ""),
            url=result.get("href", ""),
            snippet=result.get("body", ""),
            source="DDGS",
        )
        for result in results or []
        if is_linkedin_profile_url(result.get("href", ""))
    ]


def is_linkedin_profile_url(url: str) -> bool:
    """Accept only HTTPS profile URLs on LinkedIn's canonical domain."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"linkedin.com", "www.linkedin.com"}
        and parsed.path.startswith("/in/")
        and len(parsed.path.removeprefix("/in/").strip("/")) > 0
    )


@tool
def search_linkedin_profiles(query: str) -> str:
    """Find public LinkedIn profile pages matching a web search query.

    Args:
        query: Search terms including the person's name and relevant context.
    """
    try:
        results = search_ddgs_profiles(query)
    except RuntimeError as error:
        return json.dumps(
            {"error": type(error).__name__, "message": str(error)},
            ensure_ascii=False,
        )
    return json.dumps(
        [result.model_dump(mode="json") for result in results],
        ensure_ascii=False,
    )