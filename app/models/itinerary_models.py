# app/models/itinerary_models.py
from datetime import date
from typing import List
from pydantic import BaseModel, Field, model_validator, ConfigDict

class PlanTripRequest(BaseModel):
    # Strip whitespace on all str fields in this model (v2-native)
    model_config = ConfigDict(str_strip_whitespace=True)

    city: str = Field(..., min_length=2, max_length=80)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days + 1 > 30:
            raise ValueError("Trip length cannot exceed 30 days")
        return self

class DayPlan(BaseModel):
    day: int
    date: date
    summary: str
    activities: List[str]

class ItineraryResponse(BaseModel):
    city: str
    start_date: date
    end_date: date
    days: List[DayPlan]
