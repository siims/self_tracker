from dataclasses import dataclass
from datetime import datetime
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class TaskView:
    name: str
    duration: int

@dataclass_json
@dataclass
class MainTemplateData:
    target_date: datetime.date
    tasks: List[TaskView]
    worker: str
    workers: List[str]
    previous_period_start: datetime.date # = periodStart.minusDays(1)
    next_period_start: datetime.date# = periodStart.plusDays(1)
    formattedSumOverFilteredTasks: str# = tasks.map { task -> task.durationInMinutes }.sum().formatMinutes()