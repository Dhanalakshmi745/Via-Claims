import logging

from claimvision_ai.llm import LLMClient, LLMError
from claimvision_ai.rag import ClaimQuestionAnswerer, Passage
from claimvision_ai.vector_store import VectorStore
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_llm_client, get_vector_store
from app.models import Claim, Document
from app.schemas.ask import AskRequest, AskResponse, CitationRead

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ask"])

DISCLAIMER = (
    "AI-generated from the uploaded documents. Verify against the original files. "
    "This is not a fraud finding or a claim decision."
)


@router.post("/claims/{claim_id}/ask", response_model=AskResponse)
def ask_about_claim(
    claim_id: int,
    payload: AskRequest,
    db: Session = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMClient = Depends(get_llm_client),
):
    if db.get(Claim, claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    hits = vector_store.search(payload.question, claim_id=claim_id, top_k=payload.top_k)
    stmt = select(Document).where(Document.claim_id == claim_id)
    filenames = {doc.id: doc.original_filename for doc in db.scalars(stmt)}

    passages = [
        Passage(
            document_id=hit.document_id,
            source_filename=filenames.get(hit.document_id, "unknown"),
            document_type=hit.document_type,
            chunk_index=hit.chunk_index,
            text=hit.text,
        )
        for hit in hits
    ]

    try:
        result = ClaimQuestionAnswerer(llm).answer(payload.question, passages)
    except LLMError:
        logger.exception("The language model failed for claim %s", claim_id)
        raise HTTPException(
            status_code=502, detail="The AI service could not answer right now"
        )

    return AskResponse(
        question=payload.question,
        answer=result.answer,
        citations=[
            CitationRead(
                number=citation.number,
                document_id=citation.passage.document_id,
                original_filename=citation.passage.source_filename,
                document_type=citation.passage.document_type,
                chunk_index=citation.passage.chunk_index,
                text=citation.passage.text,
            )
            for citation in result.citations
        ],
        disclaimer=DISCLAIMER,
    )