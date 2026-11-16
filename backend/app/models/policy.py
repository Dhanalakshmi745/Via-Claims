from datetime import date

from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_number: Mapped[str] = mapped_column(String(50), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    vehicle_make_model: Mapped[str] = mapped_column(String(150))
    vehicle_registration: Mapped[str] = mapped_column(String(30))
    coverage_type: Mapped[str] = mapped_column(String(50))
    coverage_limit: Mapped[float] = mapped_column(Numeric(12, 2))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    customer: Mapped["Customer"] = relationship(back_populates="policies")
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")