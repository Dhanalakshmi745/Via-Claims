from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class CitationRead(BaseModel):
    number: int
    document_id: int
    original_filename: str
    document_type: str
    chunk_index: int
    text: str


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationRead]
    disclaimer: str