import logging
import uuid
from contextlib import suppress
from pathlib import Path

from claimvision_ai.chunker import chunk_text
from claimvision_ai.pdf_processor import PdfProcessingError, extract_text_from_pdf
from claimvision_ai.vector_store import VectorStore
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_vector_store
from app.models import Claim, Document
from app.schemas.document import DocumentRead, DocumentTextRead, DocumentType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])

PDF_SIGNATURE = b"%PDF-"


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/claims/{claim_id}/documents", response_model=DocumentRead, status_code=201)
def upload_document(
    claim_id: int,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
):
    if db.get(Claim, claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File is larger than {settings.max_upload_mb} MB"
        )

    if not content.startswith(PDF_SIGNATURE):
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    try:
        result = extract_text_from_pdf(content)
    except PdfProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    stored_filename = f"{uuid.uuid4().hex}.pdf"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / stored_filename

    document = Document(
        claim_id=claim_id,
        document_type=document_type,
        original_filename=Path(file.filename or "upload.pdf").name[:255],
        stored_filename=stored_filename,
        size_bytes=len(content),
        page_count=result.page_count,
        extraction_status="EXTRACTED" if result.has_text else "NO_TEXT",
        extracted_text=result.text or None,
    )
    db.add(document)
    db.flush()
    document_id = document.id

    try:
        if result.has_text:
            vector_store.index_document(
                document_id=document_id,
                claim_id=claim_id,
                document_type=document_type,
                chunks=chunk_text(result.text),
            )
        stored_path.write_bytes(content)
        db.commit()
    except Exception:
        logger.exception("Could not index document for claim %s", claim_id)
        db.rollback()
        stored_path.unlink(missing_ok=True)
        with suppress(Exception):
            vector_store.delete_document(document_id)
        raise HTTPException(
            status_code=503,
            detail="Document could not be indexed, so nothing was saved",
        )

    db.refresh(document)
    return document


@router.get("/claims/{claim_id}/documents", response_model=list[DocumentRead])
def list_claim_documents(claim_id: int, db: Session = Depends(get_db)):
    if db.get(Claim, claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    stmt = select(Document).where(Document.claim_id == claim_id).order_by(Document.id)
    return db.scalars(stmt).all()


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)):
    return get_document_or_404(db, document_id)


@router.get("/documents/{document_id}/text", response_model=DocumentTextRead)
def get_document_text(document_id: int, db: Session = Depends(get_db)):
    return get_document_or_404(db, document_id)