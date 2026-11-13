"""Agent 1: extract explicit search criteria from a free-form request."""

from langchain_core.prompts import ChatPromptTemplate

from config import create_chat_model
from schemas import SearchCriteria


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extrais les critères utiles à une recherche de profil professionnel. "
            "Conserve le nom tel qu'il est écrit. N'invente ni lieu, ni métier, "
            "ni entreprise. Laisse les champs absents vides.",
        ),
        ("user", "{request}"),
    ]
)


def extract_search_criteria(request: str) -> SearchCriteria:
    """Parse a user request into validated search criteria."""
    extractor = create_chat_model().with_structured_output(SearchCriteria)
    return (PROMPT | extractor).invoke({"request": request})