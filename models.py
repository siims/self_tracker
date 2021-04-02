from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float, Integer, Text, Date, DateTime, create_engine, Index
import datetime

Base = declarative_base()


class TimeTapDto(BaseModel):
    name: str
    worker: str
    date: datetime.date


class TimeTap(Base):
    __tablename__ = 'time_tap'

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker = Column(String(20), nullable=False, index=True)
    name = Column(Text, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    minutes = Column(Integer, default=0)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
