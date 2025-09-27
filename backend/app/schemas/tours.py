from pydantic import BaseModel
from typing import Optional, List

class TourBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: str

class TourCreate(TourBase):
    pass

class TourOut(TourBase):
    id: int

    model_config = {"from_attributes": True}

# Extended Tour model for conversational planning
class Tour(BaseModel):
    id: Optional[str] = None
    day: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    itinerary: Optional[List[str]] = None
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    accommodation: Optional[str] = None
    activities: Optional[str] = None
    transportation: Optional[str] = None
    dining: Optional[str] = None
    special_requests: Optional[str] = None

class TourCreateRequest(BaseModel):
    day: str
    location: str
    start_date: str

class ChatQuery(BaseModel):
    user_id: Optional[str] = "default_user"
    query: Optional[str] = None
    day: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    accommodation: Optional[str] = None
    activities: Optional[str] = None
    transportation: Optional[str] = None
    dining: Optional[str] = None
    special_requests: Optional[str] = None
