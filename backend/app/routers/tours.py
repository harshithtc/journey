from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Tour
from app.schemas import TourCreate, TourOut

router = APIRouter(prefix="/tours", tags=["tours"])

@router.post("/", response_model=TourOut, status_code=201)
def create_tour(tour: TourCreate, db: Session = Depends(get_db)):
    entity = Tour(**tour.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity

@router.get("/", response_model=list[TourOut])
def list_tours(db: Session = Depends(get_db)):
    return db.query(Tour).all()

@router.get("/{tour_id}", response_model=TourOut)
def get_tour(tour_id: int, db: Session = Depends(get_db)):
    obj = db.get(Tour, tour_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Tour not found")
    return obj
