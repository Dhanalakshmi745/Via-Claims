from claimvision_ai.vector_store import VectorStore
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_vector_store
from app.models import Claim, Document
from app.schemas.search import SearchHit

router = APIRouter(tags=["Search"])


@router.get("/claims/{claim_id}/search", response_model=list[SearchHit])
def search_claim_documents(
    claim_id: int,
    q: str = Query(min_length=3, max_length=500),
    top_k: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
):
    if db.get(Claim, claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    results = vector_store.search(q, claim_id=claim_id, top_k=top_k)

    stmt = select(Document).where(Document.claim_id == claim_id)
    filenames = {doc.id: doc.original_filename for doc in db.scalars(stmt)}

    return [
        SearchHit(
            document_id=result.document_id,
            original_filename=filenames.get(result.document_id),
            document_type=result.document_type,
            chunk_index=result.chunk_index,
            text=result.text,
            distance=result.distance,
        )
        for result in results
    ]