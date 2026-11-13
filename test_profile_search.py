import profile_search
from profile_validation import normalize_text, validate_candidate
from schemas import SearchCriteria, SearchResult


def test_normalize_text_removes_accents_and_punctuation() -> None:
    assert normalize_text("Élodie D’Artagnan-Smith") == "elodie d artagnan smith"


def test_validate_candidate_returns_score_and_unverified_fields() -> None:
    candidate = validate_candidate(
        SearchResult(
            title="Franck Essome — Ingénieur chez BNBXTECH",
            url="https://www.linkedin.com/in/franck-essome",
            snippet="Basé à Orsay, France",
            source="DDGS",
        ),
        SearchCriteria(
            name="Franck Essome",
            role="Ingénieur",
            company="BNBXTECH",
            location="Orsay, France",
        ),
    )

    assert candidate.match_score == 100
    assert candidate.matched_fields == ["name", "company", "role", "location"]
    assert candidate.unknown_fields == []
    assert candidate.sources == ["DDGS"]


def test_validate_candidate_does_not_infer_missing_fields() -> None:
    candidate = validate_candidate(
        SearchResult(
            title="Franck Essome | LinkedIn",
            url="https://www.linkedin.com/in/franck-essome",
            snippet="Profil professionnel public",
            source="DDGS",
        ),
        SearchCriteria(
            name="Franck Essome",
            role="Ingénieur",
            company="BNBXTECH",
        ),
    )

    assert candidate.match_score == 47
    assert candidate.matched_fields == ["name"]
    assert candidate.unknown_fields == ["company", "role"]


def test_serpapi_is_only_used_after_unreliable_prior_results(monkeypatch) -> None:
    calls: list[str] = []

    def candidate(source: str) -> list[SearchResult]:
        return [
            SearchResult(
                title="Franck Essome — Ingénieur chez BNBXTECH",
                url="https://www.linkedin.com/in/franck-essome",
                snippet="Orsay, France",
                source=source,
            )
        ]

    monkeypatch.setattr(
        profile_search,
        "search_ddgs_profiles",
        lambda query: (calls.append("DDGS") or []),
    )
    monkeypatch.setattr(
        profile_search,
        "_brave_search",
        lambda query, api_key: (calls.append("Brave") or []),
    )
    monkeypatch.setattr(
        profile_search,
        "_exa_search",
        lambda query, api_key: (calls.append("Exa") or []),
    )
    monkeypatch.setattr(
        profile_search,
        "_serpapi_search",
        lambda query, api_key: (calls.append("SerpApi") or candidate("SerpApi")),
    )

    outcome = profile_search.search_profiles(
        SearchCriteria(name="Franck Essome"),
        env={
            "BRAVE_SEARCH_API_KEY": "brave-test-key",
            "EXA_API_KEY": "exa-test-key",
            "SERPAPI_API_KEY": "serpapi-test-key",
        },
    )

    assert calls == ["DDGS", "Brave", "Exa", "SerpApi"]
    assert outcome.candidates[0].sources == ["SerpApi"]


def test_satisfactory_candidate_stops_before_serpapi(monkeypatch) -> None:
    calls: list[str] = []

    def results(source: str) -> list[SearchResult]:
        return [
            SearchResult(
                title="Franck Essome",
                url="https://www.linkedin.com/in/franck-essome",
                snippet="",
                source=source,
            )
        ]

    monkeypatch.setattr(
        profile_search,
        "search_ddgs_profiles",
        lambda query: (calls.append("DDGS") or results("DDGS")),
    )
    monkeypatch.setattr(
        profile_search,
        "_brave_search",
        lambda query, api_key: calls.append("Brave"),
    )
    monkeypatch.setattr(
        profile_search,
        "_exa_search",
        lambda query, api_key: calls.append("Exa"),
    )
    monkeypatch.setattr(
        profile_search,
        "_serpapi_search",
        lambda query, api_key: calls.append("SerpApi"),
    )

    outcome = profile_search.search_profiles(
        SearchCriteria(name="Franck Essome"),
        env={
            "BRAVE_SEARCH_API_KEY": "brave-test-key",
            "EXA_API_KEY": "exa-test-key",
            "SERPAPI_API_KEY": "serpapi-test-key",
        },
    )

    assert calls == ["DDGS"]
    assert outcome.candidates[0].match_score == 100
