from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Claim, Customer, Policy
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate

router = APIRouter(prefix="/policies", tags=["Policies"])


def get_policy_or_404(db: Session, policy_id: int) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("", response_model=PolicyRead, status_code=201)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    duplicate = db.scalar(select(Policy).where(Policy.policy_number == payload.policy_number))
    if duplicate:
        raise HTTPException(status_code=409, detail="A policy with this number already exists")

    policy = Policy(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("", response_model=list[PolicyRead])
def list_policies(
    customer_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Policy).order_by(Policy.id)
    if customer_id is not None:
        stmt = stmt.where(Policy.customer_id == customer_id)
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    return get_policy_or_404(db, policy_id)


@router.patch("/{policy_id}", response_model=PolicyRead)
def update_policy(policy_id: int, payload: PolicyUpdate, db: Session = Depends(get_db)):
    policy = get_policy_or_404(db, policy_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    new_end_date = changes.get("end_date")
    if new_end_date and new_end_date <= policy.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    for field, value in changes.items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = get_policy_or_404(db, policy_id)
    has_claims = db.scalar(select(Claim.id).where(Claim.policy_id == policy_id).limit(1))
    if has_claims:
        raise HTTPException(status_code=409, detail="Policy has claims and cannot be deleted")

    db.delete(policy)
    db.commit()