"""Evidence-based matching for public profile search results."""

import re
import unicodedata

from schemas import ProfileCandidate, SearchCriteria, SearchResult


_FIELD_WEIGHTS = {
    "name": 40,
    "company": 25,
    "role": 20,
    "location": 15,
}


def normalize_text(value: str) -> str:
    """Normalize accents, punctuation, and whitespace for conservative matching."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[a-z0-9]+", without_accents))


def _matches(expected: str, evidence: str) -> bool:
    expected_tokens = normalize_text(expected).split()
    normalized_evidence_tokens = normalize_text(evidence).split()
    evidence_tokens = set(normalized_evidence_tokens)
    if not expected_tokens:
        return False

    phrase_matches = any(
        normalized_evidence_tokens[index:index + len(expected_tokens)]
        == expected_tokens
        for index in range(
            len(normalized_evidence_tokens) - len(expected_tokens) + 1
        )
    )
    return (
        phrase_matches
        or set(expected_tokens).issubset(evidence_tokens)
    )


def validate_candidate(
    result: SearchResult,
    criteria: SearchCriteria,
) -> ProfileCandidate:
    """Score only requested criteria and list those not evidenced in the result."""
    evidence = f"{result.title} {result.snippet}"
    requested = {
        "name": criteria.name,
        "company": criteria.company,
        "role": criteria.role,
        "location": criteria.location,
    }
    active_fields = {
        field: value.strip()
        for field, value in requested.items()
        if value and value.strip()
    }
    matched_fields = [
        field for field, value in active_fields.items()
        if _matches(value, evidence)
    ]
    unknown_fields = [
        field for field in active_fields
        if field not in matched_fields
    ]
    total_weight = sum(_FIELD_WEIGHTS[field] for field in active_fields)
    match_score = round(
        100
        * sum(_FIELD_WEIGHTS[field] for field in matched_fields)
        / total_weight
    ) if total_weight else 0

    return ProfileCandidate(
        title=result.title,
        url=result.url,
        snippet=result.snippet,
        sources=[result.source],
        match_score=match_score,
        matched_fields=matched_fields,
        unknown_fields=unknown_fields,
    )
