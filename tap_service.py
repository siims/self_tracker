import datetime
from typing import List, Optional, Any

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from models import Base, TimeTap, NoteTap, NoteTapDto, TimeTapDto, MedicationTap, Medication, MedicationTapDto, \
    MedicationDto
from views import TimeTapView, NoteTapView, MedicationTapView

engine = create_engine(
    "sqlite:///app.db",
    connect_args={"check_same_thread": False}
)

Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


class InvalidInputException(Exception):
    ...


def fetch_time_tap(
        worker: Optional[str] = None,
        target_date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> Optional[TimeTapView]:
    res = fetch_time_taps(worker=worker, target_date=target_date, name=name)
    if len(res) == 0:
        return None
    else:
        return TimeTapView(name=res[0].name, duration=res[0].duration)


def fetch_time_taps(
        worker: Optional[str] = None,
        target_date: Optional[datetime.date] = None,
        first_date: Optional[datetime.date] = None,
        last_date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> List[TimeTapView]:
    where = []
    group_by = [TimeTap.name]
    if worker is not None:
        where.append(TimeTap.worker == worker)
    if target_date is not None:
        where.append(TimeTap.date == target_date)
        group_by.append(TimeTap.date)
    if first_date is not None:
        where.append(TimeTap.date >= first_date)
    if last_date is not None:
        where.append(TimeTap.date <= last_date)
    if name is not None:
        where.append(TimeTap.name == name)

    res = session.query(
        TimeTap.name,
        func.sum(TimeTap.minutes).label("duration"),
        func.max(TimeTap.created).label("last_created")
    ).where(
        *where
    ).group_by(
        *group_by
    ).all()
    return [TimeTapView(name=x.name, duration=x.duration) for x in res]


def add_time_tap(time_tap: TimeTapDto, minutes: int) -> None:
    new_tap = TimeTap(
        worker=time_tap.worker,
        date=time_tap.date,
        name=time_tap.name,
        minutes=minutes
    )
    session.add(new_tap)
    session.commit()


def fetch_medication_taps(
        worker: Optional[str] = None,
        date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> List[Any]:
    where = [MedicationTap.is_deleted == False]
    if worker is not None:
        where.append(MedicationTap.worker == worker)
    if date is not None:
        where.append(MedicationTap.date == date)
    if name is not None:
        where.append(Medication.name == name)
    res = session.query(MedicationTap, Medication).join(Medication).where(*where).all()
    return res


def get_medication_views(
        worker: Optional[str] = None,
        date: Optional[datetime.date] = None,
        name: Optional[str] = None
) -> List[MedicationTapView]:
    medication_taps = fetch_medication_taps(worker=worker, date=date, name=name)

    return [
        MedicationTapView(name=tap["Medication"].name, doses=tap["MedicationTap"].doses)
        for tap in medication_taps
    ]


def update_medication_tap(medication_tap: MedicationTapDto, dose_taken: int) -> MedicationTapView:
    medication = session.query(Medication).where(Medication.name == medication_tap.name).first()
    new_tap = session.query(MedicationTap).where(
        MedicationTap.worker == medication_tap.worker,
        MedicationTap.date == medication_tap.date,
        MedicationTap.medication == medication.id
    ).one_or_none()

    if new_tap is None:
        new_tap = MedicationTap(
            worker=medication_tap.worker,
            date=medication_tap.date,
            doses=1,
            medication=medication.id)
        session.add(new_tap)
    else:
        new_tap.doses += dose_taken
    session.commit()

    return MedicationTapView(name=medication_tap.name, doses=new_tap.doses)


def get_unused_time_tap_blocks_for_day(used_time_tap_names: List[str]) -> List[TimeTapView]:
    missing_tap_names = list(set(fetch_all_task_names()) - set(used_time_tap_names))
    unsused_time_tap_views = [TimeTapView(name=name, duration=0) for name in missing_tap_names]
    unsused_time_tap_views.sort(key=lambda x: x.name)
    return unsused_time_tap_views


def get_unused_medication_tap_blocks_for_day(used_medication_tap_names: List[str]) -> List[MedicationTapView]:
    missing_tap_names = list(set(fetch_all_medication_names()) - set(used_medication_tap_names))
    unsused_medication_tap_views = [MedicationTapView(name=name, doses=0) for name in missing_tap_names]
    unsused_medication_tap_views.sort(key=lambda x: x.name)
    return unsused_medication_tap_views


def fetch_all_task_names() -> List[str]:
    return [task.name for task in session.query(TimeTap.name).group_by(TimeTap.name).all()]


def fetch_all_medication_names() -> List[str]:
    return [medication.name for medication in session.query(Medication).all()]


def fetch_all_workers() -> List[str]:
    return [task.worker for task in session.query(TimeTap.worker).group_by(TimeTap.worker).all()]


def fetch_note_taps(worker: Optional[str] = None, date: Optional[datetime.date] = None) -> List[NoteTapView]:
    where = [NoteTap.is_deleted == False]
    if worker is not None:
        where.append(NoteTap.worker == worker)
    if date is not None:
        where.append(NoteTap.date == date)
    note_taps = session.query(NoteTap).where(
        *where
    ).all()
    return [NoteTapView(id=e.id, type=e.type, description=e.description) for e in note_taps]


def add_note_tap(note: NoteTapDto) -> NoteTapDto:
    new_tap = NoteTap(
        worker=note.worker,
        date=note.date,
        type=note.type,
        description=note.description,
    )
    session.add(new_tap)
    session.commit()

    return NoteTapDto(
        id=new_tap.id,
        worker=new_tap.worker,
        date=new_tap.date,
        type=new_tap.type,
        description=new_tap.description,
    )


def delete_note_tap(note: NoteTapDto):
    where = [NoteTap.worker == note.worker, NoteTap.date == note.date, NoteTap.description == note.description,
             NoteTap.is_deleted == False]
    if note.type is None:
        where.append(NoteTap.type == note.type)
    notes = session.query(NoteTap).where(
        *where
    ).all()
    if len(notes) == 0:
        raise InvalidInputException(f"Note doesn't exist: {note}")
    notes[0].is_deleted = True
    session.commit()


def add_medication(medication: MedicationDto) -> None:
    new_medication = Medication(name=medication.name)
    session.add(new_medication)
    session.commit()

