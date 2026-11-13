"""Build deterministic search queries from extracted criteria."""

from schemas import SearchCriteria


def build_search_query(criteria: SearchCriteria) -> str:
    """Combine non-empty criteria into a compact web search query."""
    terms = [
        criteria.name,
        criteria.role,
        criteria.company,
        criteria.location,
        *criteria.keywords,
    ]
    return " ".join(term.strip() for term in terms if term and term.strip())