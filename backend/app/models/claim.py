from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, Numeric, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_number: Mapped[str] = mapped_column(String(50), unique=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"))
    incident_date: Mapped[date] = mapped_column(Date)
    incident_description: Mapped[str] = mapped_column(Text)
    claimed_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    policy: Mapped["Policy"] = relationship(back_populates="claims")
    documents: Mapped[list["Document"]] = relationship(back_populates="claim")