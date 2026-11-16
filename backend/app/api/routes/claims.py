from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Claim, Policy
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimStatus, ClaimUpdate

router = APIRouter(prefix="/claims", tags=["Claims"])


def get_claim_or_404(db: Session, claim_id: int) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("", response_model=ClaimRead, status_code=201)
def create_claim(payload: ClaimCreate, db: Session = Depends(get_db)):
    policy = db.get(Policy, payload.policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    duplicate = db.scalar(select(Claim).where(Claim.claim_number == payload.claim_number))
    if duplicate:
        raise HTTPException(status_code=409, detail="A claim with this number already exists")

    if not (policy.start_date <= payload.incident_date <= policy.end_date):
        raise HTTPException(
            status_code=400,
            detail="Incident date falls outside the policy period",
        )

    claim = Claim(**payload.model_dump(), status="SUBMITTED")
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("", response_model=list[ClaimRead])
def list_claims(
    policy_id: int | None = None,
    status_filter: ClaimStatus | None = Query(default=None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Claim).order_by(Claim.id)
    if policy_id is not None:
        stmt = stmt.where(Claim.policy_id == policy_id)
    if status_filter is not None:
        stmt = stmt.where(Claim.status == status_filter)
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@router.get("/{claim_id}", response_model=ClaimRead)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    return get_claim_or_404(db, claim_id)


@router.patch("/{claim_id}", response_model=ClaimRead)
def update_claim(claim_id: int, payload: ClaimUpdate, db: Session = Depends(get_db)):
    claim = get_claim_or_404(db, claim_id)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(claim, field, value)
    db.commit()
    db.refresh(claim)
    return claim