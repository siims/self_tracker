from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float, Integer, Text, Date, DateTime, create_engine
import datetime

Base = declarative_base()

class TimeTapDto(BaseModel):
    name: str
    worker: str
    date: datetime.date

class TimeTap(Base):
    __tablename__ = 'time_tap'

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker = Column(String(20), nullable=False)
    name = Column(Text, nullable=False)
    minutes = Column(Integer, default=0)
    date = Column(Date, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
