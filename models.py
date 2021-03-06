import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Text, Date, DateTime, Index, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TimeTapDto(BaseModel):
    name: str
    date: datetime.date
    user_email: Optional[str]


class MedicationDto(BaseModel):
    name: str


class MedicationTapDto(BaseModel):
    name: str
    user_email: str
    date: datetime.date


class NoteTapDto(BaseModel):
    id: Optional[str]
    type: Optional[str]
    description: str
    user_email: str
    date: datetime.date


class TimeTapStatisticsRequestDto(BaseModel):
    user_email: str
    first_date: datetime.date
    last_date: datetime.date


class TimeTapStatisticsResponseDto(BaseModel):
    task_name: str
    minutes: int
    last_action: datetime.datetime


class AbstractTap(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(Text, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)


class TimeTap(AbstractTap):
    __tablename__ = "time_tap"

    name = Column(Text, nullable=False, index=True)
    minutes = Column(Integer, default=0)


class ActiveSubstance(Base):
    __tablename__ = "medication_active_substance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    medication_single_dose_size = Column(Integer, ForeignKey('medication_single_dose.id'))


class MedicationSingleDoseSize(Base):
    __tablename__ = "medication_single_dose"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dose_size = Column(Float)
    medication = Column(Integer, ForeignKey('medication.id'))

    active_substances = relationship("ActiveSubstance")


class Medication(Base):
    __tablename__ = "medication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    medication_single_dose_sizes = relationship("MedicationSingleDoseSize")


class MedicationTap(AbstractTap):
    __tablename__ = "medication_tap"

    doses = Column(Integer, nullable=False, default=0)
    medication = Column(Integer, ForeignKey('medication.id'))


Index('time_tap_user_email_x_date', TimeTap.user_email, TimeTap.date)
Index('time_tap_user_email_x_date_x_name', TimeTap.user_email, TimeTap.date, TimeTap.name)


class NoteTap(AbstractTap):
    __tablename__ = "notes"

    type = Column(Text, index=True)
    description = Column(Text, nullable=False)
