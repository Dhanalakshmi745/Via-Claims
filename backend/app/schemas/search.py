from pydantic import BaseModel


class SearchHit(BaseModel):
    document_id: int
    original_filename: str | None
    document_type: str
    chunk_index: int
    text: str
    distance: float