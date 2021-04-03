import datetime
import logging

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from models import TimeTapDto, NoteTapDto, TimeTapStatisticsRequestDto, MedicationTapDto
from tap_service import fetch_time_taps, fetch_time_tap, fetch_all_workers, fetch_note_taps, \
    delete_note_tap, InvalidInputException, add_note_tap, add_time_tap, get_unused_time_tap_blocks_for_day, \
    get_medication_views, update_medication_tap, get_unused_medication_tap_blocks_for_day
from views import MainTemplateData

templates = Jinja2Templates(directory="templates/")
log = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
async def homepage(request: Request, worker: str, target_date: datetime.date = datetime.date.today()):
    time_tap_views = fetch_time_taps(worker=worker, target_date=target_date)
    unused_time_tap_views = get_unused_time_tap_blocks_for_day([tap.name for tap in time_tap_views])
    medication_tap_views = get_medication_views(worker=worker, date=target_date)
    unused_medication_tap_views = get_unused_medication_tap_blocks_for_day([tap.name for tap in medication_tap_views])
    note_taps = fetch_note_taps(worker=worker, date=target_date)
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            **MainTemplateData(
                target_date=target_date,
                time_taps=time_tap_views + unused_time_tap_views,
                note_taps=note_taps,
                medication_taps=medication_tap_views + unused_medication_tap_views,
                worker=worker,
                workers=fetch_all_workers(),
                previous_period_start=target_date + datetime.timedelta(days=-1),
                next_period_start=target_date + datetime.timedelta(days=1),
            ).to_dict()
        }
    )


@app.get("/summary")
async def summary_page(request: Request, worker: str):
    if worker == "":
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "summary.html",
        context={
            "request": request,
            "worker": worker
        }
    )


@app.post("/time_tap")
async def post_time_tap(time_tap: TimeTapDto):
    if time_tap.worker == "":
        raise HTTPException(status_code=400, detail="Invalid input")
    add_time_tap(time_tap, minutes=15)

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.delete("/time_tap")
async def delete_time_tap(time_tap: TimeTapDto):
    tap = fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)
    if tap is not None and tap.duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid input, cannot have negative total time")

    add_time_tap(time_tap, minutes=-15)

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.post("/note_tap")
async def post_a_note(note: NoteTapDto):
    if note.worker == "":
        raise HTTPException(status_code=400, detail="Invalid input")
    return add_note_tap(note)


@app.delete("/note_tap")
async def post_a_note(note: NoteTapDto):
    try:
        delete_note_tap(note)
    except InvalidInputException as e:
        log.warning(e)
        raise HTTPException(status_code=400, detail="Invalid input")


@app.post("/medication_tap")
async def post_time_tap(medication_tap: MedicationTapDto):
    if medication_tap.worker == "":
        raise HTTPException(status_code=400, detail="Invalid input")

    update_medication_tap(medication_tap, dose_taken=1)

    return get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)[0]


@app.delete("/medication_tap")
async def delete_time_tap(medication_tap: MedicationTapDto):
    tap = get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)
    if len(tap) == 0 or tap[0].doses <= 0:
        raise HTTPException(status_code=400, detail="Invalid input")

    update_medication_tap(medication_tap, dose_taken=-1)

    return get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)[0]


@app.post("/statistics")
async def time_tap_statistics(note: TimeTapStatisticsRequestDto):
    if note.worker == "":
        raise HTTPException(status_code=400, detail="Invalid input")
    return fetch_time_taps(worker=note.worker, first_date=note.first_date, last_date=note.last_date)


@app.get("/favicon.ico")
async def get_favicon():
    return RedirectResponse("/static/favicon.ico")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":  # for debugging
    uvicorn.run(app, host="0.0.0.0", port=8000)
