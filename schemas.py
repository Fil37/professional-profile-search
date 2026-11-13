"""Validated data structures exchanged by the search workflow."""

from pydantic import BaseModel, Field, HttpUrl


class SearchCriteria(BaseModel):
    """Explicit details extracted from the user's search request."""

    name: str = Field(default="", description="Full name of the target person")
    role: str = Field(default="", description="Profession or current role")
    company: str = Field(default="", description="Company or organization")
    location: str = Field(default="", description="Explicit city, region, or country")
    keywords: list[str] = Field(
        default_factory=list,
        description="Other explicit search terms from the request",
    )


class SearchResult(BaseModel):
    """A search-engine result for a publicly indexed profile."""

    title: str = ""
    url: HttpUrl
    snippet: str = ""
    source: str


class ProfileCandidate(BaseModel):
    """A candidate with evidence-based matching details."""

    title: str
    url: HttpUrl
    snippet: str
    sources: list[str]
    match_score: int = Field(ge=0, le=100)
    matched_fields: list[str]
    unknown_fields: list[str]


class SearchOutcome(BaseModel):
    """Candidates and provider issues returned by the search pipeline."""

    candidates: list[ProfileCandidate]
    provider_errors: list[str] = Field(default_factory=list)
    skipped_providers: list[str] = Field(default_factory=list)