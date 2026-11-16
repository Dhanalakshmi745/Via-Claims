from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ClaimStatus = Literal["SUBMITTED", "UNDER_REVIEW", "INFO_REQUESTED", "CLOSED"]


class ClaimCreate(BaseModel):
    claim_number: str = Field(min_length=3, max_length=50)
    policy_id: int = Field(gt=0)
    incident_date: date
    incident_description: str = Field(min_length=10)
    claimed_amount: float = Field(gt=0)

    @field_validator("incident_date")
    @classmethod
    def incident_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("incident_date cannot be in the future")
        return value


class ClaimUpdate(BaseModel):
    incident_description: str | None = Field(default=None, min_length=10)
    claimed_amount: float | None = Field(default=None, gt=0)
    status: ClaimStatus | None = None


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_number: str
    policy_id: int
    incident_date: date
    incident_description: str
    claimed_amount: float
    status: str
    created_at: datetime