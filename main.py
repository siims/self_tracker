import datetime
from functools import reduce

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from dao import session, fetch_time_taps, fetch_all_task_names, fetch_time_tap, fetch_all_workers
from models import TimeTap, TimeTapDto
from views import MainTemplateData, TaskView

templates = Jinja2Templates(directory="templates/")

app = FastAPI()


@app.get("/")
async def homepage(request: Request, worker: str, target_date: datetime.date = datetime.date.today()):
    time_taps = fetch_time_taps(worker=worker, target_date=target_date)
    time_taps = [TaskView(name=item.name, duration=item.duration) for item in time_taps]
    missing_task_names = [TaskView(name=name, duration=0) for name in
                          set(fetch_all_task_names()) - set([tap.name for tap in time_taps])]
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            **MainTemplateData(
                target_date=target_date,
                tasks=time_taps + missing_task_names,
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


@app.get("/time_tap")
async def get_all_time_taps(worker: str):
    time_taps = session.query(
        TimeTap,
        func.sum(TimeTap.minutes).label("duration"),
        func.max(TimeTap.created).label("last_created")
    ).where(
        TimeTap.worker == worker).group_by("task_name", "target_date").all()
    res = reduce(lambda x, y: {**x, **y}, map(lambda item: {
        item["TimeTap"].task_name: {"id": item["TimeTap"].task_name, "name": item["TimeTap"].task_name,
                                    "duration": item.duration}}, time_taps), {})
    return jsonable_encoder(res)

@app.get("/favicon.ico")
async def get_favicon():
    return RedirectResponse("/static/favicon.ico")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__": # for debugging
    uvicorn.run(app, host="0.0.0.0", port=8000)
