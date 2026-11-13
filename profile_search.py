"""Ordered public-profile search with SerpApi as the final fallback."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from profile_validation import validate_candidate
from query_builder import build_search_query
from schemas import ProfileCandidate, SearchCriteria, SearchOutcome, SearchResult
from linkedin_search import (
    is_linkedin_profile_url,
    search_ddgs_profiles,
)


MATCH_THRESHOLD = 65
REQUEST_TIMEOUT_SECONDS = 12


def _request_json(
    provider: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if body is not None else {}),
            **(headers or {}),
        },
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(
            f"{provider} request failed with HTTP {error.code}"
        ) from error
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"{provider} request failed: {type(error).__name__}"
        ) from error


def _brave_search(query: str, api_key: str) -> list[SearchResult]:
    url = "https://api.search.brave.com/res/v1/web/search?" + urlencode(
        {"q": f"site:linkedin.com/in/ {query}", "count": 10}
    )
    payload = _request_json(
        "Brave",
        url,
        headers={"X-Subscription-Token": api_key},
    )
    web = payload.get("web", {})
    results = web.get("results", []) if isinstance(web, dict) else []
    return [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("description", ""),
            source="Brave",
        )
        for item in results
        if isinstance(item, dict) and is_linkedin_profile_url(item.get("url", ""))
    ]


def _exa_search(query: str, api_key: str) -> list[SearchResult]:
    payload = _request_json(
        "Exa",
        "https://api.exa.ai/search",
        headers={"x-api-key": api_key},
        body={
            "query": query,
            "includeDomains": ["linkedin.com"],
            "numResults": 10,
            "contents": {"text": {"maxCharacters": 1000}},
        },
    )
    results = payload.get("results", [])
    return [
        SearchResult(
            title=item.get("title") or "",
            url=item.get("url", ""),
            snippet=item.get("text") or "",
            source="Exa",
        )
        for item in results
        if isinstance(item, dict) and is_linkedin_profile_url(item.get("url", ""))
    ]


def _serpapi_search(query: str, api_key: str) -> list[SearchResult]:
    url = "https://serpapi.com/search.json?" + urlencode(
        {
            "engine": "google",
            "q": f"site:linkedin.com/in/ {query}",
            "api_key": api_key,
            "num": 10,
        }
    )
    payload = _request_json("SerpApi", url)
    results = payload.get("organic_results", [])
    return [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            source="SerpApi",
        )
        for item in results
        if isinstance(item, dict) and is_linkedin_profile_url(item.get("link", ""))
    ]


def _merge_candidate(
    candidates: dict[str, ProfileCandidate],
    candidate: ProfileCandidate,
) -> None:
    canonical_url = str(candidate.url).split("?", maxsplit=1)[0].rstrip("/")
    existing = candidates.get(canonical_url)
    if existing is None:
        candidates[canonical_url] = candidate
        return

    sources = list(dict.fromkeys([*existing.sources, *candidate.sources]))
    if candidate.match_score > existing.match_score:
        candidate.sources = sources
        candidates[canonical_url] = candidate
    else:
        existing.sources = sources


def _has_satisfactory_candidate(
    candidates: dict[str, ProfileCandidate],
) -> bool:
    return any(
        candidate.match_score >= MATCH_THRESHOLD
        and "name" in candidate.matched_fields
        for candidate in candidates.values()
    )


def search_profiles(
    criteria: SearchCriteria,
    *,
    env: dict[str, str] | None = None,
) -> SearchOutcome:
    """Search DDGS, Brave, Exa, then SerpApi only while results remain weak."""
    settings = os.environ if env is None else env
    query = build_search_query(criteria)
    candidates: dict[str, ProfileCandidate] = {}
    errors: list[str] = []
    skipped: list[str] = []

    providers = [
        (
            "DDGS",
            lambda: search_ddgs_profiles(query),
            None,
        ),
        (
            "Brave",
            lambda: _brave_search(query, settings["BRAVE_SEARCH_API_KEY"]),
            "BRAVE_SEARCH_API_KEY",
        ),
        (
            "Exa",
            lambda: _exa_search(query, settings["EXA_API_KEY"]),
            "EXA_API_KEY",
        ),
        (
            "SerpApi",
            lambda: _serpapi_search(query, settings["SERPAPI_API_KEY"]),
            "SERPAPI_API_KEY",
        ),
    ]

    for name, search, key_name in providers:
        if _has_satisfactory_candidate(candidates):
            break
        if key_name and not settings.get(key_name):
            skipped.append(f"{name} ignoré : {key_name} n'est pas configurée.")
            continue
        try:
            results = search()
        except Exception as error:
            errors.append(f"{name} : {error}")
            continue

        for result in results:
            _merge_candidate(candidates, validate_candidate(result, criteria))

    ranked_candidates = sorted(
        candidates.values(),
        key=lambda candidate: candidate.match_score,
        reverse=True,
    )
    return SearchOutcome(
        candidates=ranked_candidates,
        provider_errors=errors,
        skipped_providers=skipped,
    )
