from pydantic import BaseModel

class TourBase(BaseModel):
    name: str
    description: str | None = None
    location: str

class TourCreate(TourBase):
    pass

class TourOut(TourBase):
    id: int

    model_config = {"from_attributes": True}
