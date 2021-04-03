import datetime
from typing import List, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from models import Base, TimeTap
from views import TimeTapView

engine = create_engine(
    "sqlite:///app.db",
    connect_args={"check_same_thread": False}
)

Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


def fetch_time_tap(
        worker: Optional[str] = None,
        target_date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> Optional[TimeTapView]:
    res = fetch_time_taps(worker, target_date, name)
    if len(res) == 0:
        return None
    else:
        return TimeTapView(name=res[0].name, duration=res[0].duration)


def fetch_time_taps(
        worker: Optional[str] = None,
        target_date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> List[TimeTapView]:
    where = []
    if worker is not None:
        where.append(TimeTap.worker == worker)
    if target_date is not None:
        where.append(TimeTap.date == target_date)
    if name is not None:
        where.append(TimeTap.name == name)

    res = session.query(
        TimeTap.name,
        func.sum(TimeTap.minutes).label("duration"),
        func.max(TimeTap.created).label("last_created")
    ).where(
        *where
    ).group_by(
        TimeTap.name, TimeTap.date
    ).all()
    return [TimeTapView(name=x.name, duration=x.duration) for x in res]


def fetch_all_task_names() -> List[str]:
    return [task.name for task in session.query(TimeTap.name).group_by(TimeTap.name).all()]


def fetch_all_workers() -> List[str]:
    return [task.worker for task in session.query(TimeTap.worker).group_by(TimeTap.worker).all()]
