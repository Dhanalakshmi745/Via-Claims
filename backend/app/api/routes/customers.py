from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Policy
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_customer_or_404(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    duplicate = db.scalar(select(Customer).where(Customer.email == payload.email))
    if duplicate:
        raise HTTPException(status_code=409, detail="A customer with this email already exists")

    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerRead])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Customer).order_by(Customer.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return get_customer_or_404(db, customer_id)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = get_customer_or_404(db, customer_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    new_email = changes.get("email")
    if new_email and new_email != customer.email:
        taken = db.scalar(select(Customer).where(Customer.email == new_email))
        if taken:
            raise HTTPException(status_code=409, detail="A customer with this email already exists")

    for field, value in changes.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = get_customer_or_404(db, customer_id)
    has_policies = db.scalar(select(Policy.id).where(Policy.customer_id == customer_id).limit(1))
    if has_policies:
        raise HTTPException(status_code=409, detail="Customer still has policies and cannot be deleted")

    db.delete(customer)
    db.commit()