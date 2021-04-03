from dataclasses import dataclass
from datetime import datetime
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class TimeTapView:
    name: str
    duration: int


@dataclass_json
@dataclass
class NoteTapView:
    id: int
    type: str
    description: str


@dataclass_json
@dataclass
class MedicationTapView:
    name: str
    doses: int


@dataclass_json
@dataclass
class MainTemplateData:
    target_date: datetime.date
    time_taps: List[TimeTapView]
    note_taps: List[NoteTapView]
    medication_taps: List[MedicationTapView]
    worker: str
    workers: List[str]
    previous_period_start: datetime.date
    next_period_start: datetime.date
