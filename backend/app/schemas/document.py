from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

DocumentType = Literal[
    "POLICE_REPORT", "REPAIR_ESTIMATE", "INVOICE", "POLICY_DOCUMENT", "OTHER"
]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_id: int
    document_type: str
    original_filename: str
    size_bytes: int
    page_count: int
    extraction_status: str
    uploaded_at: datetime


class DocumentTextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extraction_status: str
    extracted_text: str | None