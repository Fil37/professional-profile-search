import json

from query_builder import build_search_query
from schemas import SearchCriteria
import linkedin_search


def test_build_search_query_uses_only_non_empty_criteria() -> None:
    criteria = SearchCriteria(
        name="Franck Essome",
        role="Ingénieur",
        company="BNBXTECH",
        location="Orsay, France",
        keywords=["machine learning"],
    )

    assert build_search_query(criteria) == (
        "Franck Essome Ingénieur BNBXTECH Orsay, France machine learning"
    )


def test_build_search_query_handles_missing_optional_criteria() -> None:
    criteria = SearchCriteria(name="Franck Essome")

    assert build_search_query(criteria) == "Franck Essome"


def test_linkedin_search_returns_dns_error_instead_of_raising(monkeypatch) -> None:
    class BrokenSearchEngine:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def text(self, *args, **kwargs):
            raise RuntimeError("DNS lookup failed")

    monkeypatch.setattr(linkedin_search, "DDGS", BrokenSearchEngine)

    response = linkedin_search.search_linkedin_profiles.invoke(
        {"query": "Franck Essome"}
    )

    assert json.loads(response) == {
        "error": "RuntimeError",
        "message": "DDGS search failed: DNS lookup failed",
    }