import datetime

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import desc
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from dao import session, fetch_time_taps, fetch_all_task_names, fetch_time_tap, fetch_all_workers
from models import TimeTap, TimeTapDto, NoteTapDto, NoteTap
from views import MainTemplateData, TimeTapView, NoteTapView

templates = Jinja2Templates(directory="templates/")

app = FastAPI()


@app.get("/")
async def homepage(request: Request, worker: str, target_date: datetime.date = datetime.date.today()):
    time_taps = fetch_time_taps(worker=worker, target_date=target_date)
    time_tap_views = [TimeTapView(name=item.name, duration=item.duration) for item in time_taps]
    missing_tap_names = list(set(fetch_all_task_names()) - set([tap.name for tap in time_tap_views]))
    missing_time_tap_views = [TimeTapView(name=name, duration=0) for name in missing_tap_names]
    missing_time_tap_views.sort(key=lambda x: x.name)

    note_taps = [NoteTapView(id=e.id, type=e.type, description=e.description) for e in session.query(NoteTap).where(NoteTap.worker == worker, NoteTap.date == target_date, NoteTap.is_deleted == False).all()]
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            **MainTemplateData(
                target_date=target_date,
                time_taps=time_tap_views + missing_time_tap_views,
                note_taps=note_taps,
                worker=worker,
                workers=fetch_all_workers(),
                previous_period_start=target_date + datetime.timedelta(days=-1),
                next_period_start=target_date + datetime.timedelta(days=1),
                formattedSumOverFilteredTasks="0"
            ).to_dict()
        }
    )


@app.post("/time_tap")
async def post_time_tap(time_tap: TimeTapDto):
    new_tap = TimeTap(
        worker=time_tap.worker,
        date=time_tap.date,
        name=time_tap.name,
        minutes=15
    )
    session.add(new_tap)
    session.commit()

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.delete("/time_tap")
async def delete_time_tap(time_tap: TimeTapDto):
    new_tap = TimeTap(
        worker=time_tap.worker,
        date=time_tap.date,
        name=time_tap.name,
        minutes=-15
    )
    session.add(new_tap)
    session.commit()

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.post("/note_tap")
async def post_a_note(note: NoteTapDto):
    new_tap = NoteTap(
        worker=note.worker,
        date=note.date,
        type=note.type,
        description=note.description,
    )
    session.add(new_tap)
    session.commit()

    return session.query(NoteTap).where(
        NoteTap.worker == note.worker, NoteTap.date == note.date, NoteTap.type == note.type, NoteTap.is_deleted == False
    ).order_by(
        desc(NoteTap.created)
    ).limit(1).one_or_none()


@app.delete("/note_tap")
async def post_a_note(note: NoteTapDto):
    where = [NoteTap.worker == note.worker, NoteTap.date == note.date, NoteTap.description == note.description, NoteTap.is_deleted == False]
    if note.type is None:
        where.append(NoteTap.type == note.type)
    notes = session.query(NoteTap).where(
        *where
    ).all()
    if len(notes) == 0:
        raise HTTPException(status_code=400, detail="Invalid input")
    notes[0].is_deleted=True
    session.commit()


@app.get("/favicon.ico")
async def get_favicon():
    return RedirectResponse("/static/favicon.ico")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":  # for debugging
    uvicorn.run(app, host="0.0.0.0", port=8000)
