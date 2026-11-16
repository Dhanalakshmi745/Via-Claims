from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CoverageType = Literal["THIRD_PARTY", "COMPREHENSIVE"]


class PolicyCreate(BaseModel):
    policy_number: str = Field(min_length=3, max_length=50)
    customer_id: int = Field(gt=0)
    vehicle_make_model: str = Field(min_length=2, max_length=150)
    vehicle_registration: str = Field(min_length=4, max_length=30)
    coverage_type: CoverageType
    coverage_limit: float = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def end_date_after_start_date(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class PolicyUpdate(BaseModel):
    vehicle_make_model: str | None = Field(default=None, min_length=2, max_length=150)
    vehicle_registration: str | None = Field(default=None, min_length=4, max_length=30)
    coverage_type: CoverageType | None = None
    coverage_limit: float | None = Field(default=None, gt=0)
    end_date: date | None = None


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_number: str
    customer_id: int
    vehicle_make_model: str
    vehicle_registration: str
    coverage_type: str
    coverage_limit: float
    start_date: date
    end_date: date