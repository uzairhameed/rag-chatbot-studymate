from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    """The question sent by the user."""

    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        """Trim surrounding whitespace and reject an empty question."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Query must contain text.")
        return cleaned_value


class SourceRead(BaseModel):
    """Citation details for one retrieved chunk."""

    filename: str
    file_type: str
    chunk_index: int
    excerpt: str


class ChatResponse(BaseModel):
    """Answer and its citations; sources is always a list."""

    answer: str
    sources: list[SourceRead]


class ChatMessageRead(BaseModel):
    """One saved user or assistant message returned in room history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[SourceRead] = Field(default_factory=list)
    created_at: datetime