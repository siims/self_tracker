import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Text, Date, DateTime, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimeTapDto(BaseModel):
    name: str
    worker: str
    date: datetime.date


class TimeTapStatisticsRequestDto(BaseModel):
    worker: str
    first_date: datetime.date
    last_date: datetime.date


class TimeTapStatisticsResponseDto(BaseModel):
    task_name: str
    minutes: int
    last_action: datetime.datetime


class NoteTapDto(BaseModel):
    id: Optional[str]
    type: Optional[str]
    description: str
    worker: str
    date: datetime.date


class AbstractTap(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)


class TimeTap(AbstractTap):
    __tablename__ = "time_tap"

    name = Column(Text, nullable=False, index=True)
    minutes = Column(Integer, default=0)


Index('time_tap_worker_x_date', TimeTap.worker, TimeTap.date)
Index('time_tap_worker_x_date_x_name', TimeTap.worker, TimeTap.date, TimeTap.name)


class NoteTap(AbstractTap):
    __tablename__ = "notes"

    type = Column(Text, index=True)
    description = Column(Text, nullable=False)
