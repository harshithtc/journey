from sqlalchemy import Column, Integer, String, Text
from app.db.session import Base

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
