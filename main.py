import datetime
import logging
from typing import Optional

import uvicorn
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request, HTTPException, Depends
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from auth import get_current_user
from models import TimeTapDto, NoteTapDto, TimeTapStatisticsRequestDto, MedicationTapDto, MedicationDto
from tap_service import fetch_time_taps, fetch_time_tap, fetch_all_workers, fetch_note_taps, \
    delete_note_tap, InvalidInputException, add_note_tap, add_time_tap, get_unused_time_tap_blocks_for_day, \
    get_medication_views, update_medication_tap, get_unused_medication_tap_blocks_for_day, add_medication
from views import MainTemplateData

templates = Jinja2Templates(directory="templates/")
log = logging.getLogger(__name__)

app = FastAPI()

config = Config(".env")
if config.get("GOOGLE_CLIENT_ID", default=None) is None \
        or config.get("GOOGLE_CLIENT_SECRET", default=None) is None \
        or config.get("SESSION_SECRET", default=None) is None:
    raise Exception("Configuration error. GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET or SESSION_SECRET not specified.")
oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

app.add_middleware(SessionMiddleware, secret_key=config.get("SESSION_SECRET"))


@app.get("/")
async def homepage(request: Request, target_date: Optional[datetime.date] = None):
    user = request.session.get('user')
    if target_date is None:
        target_date = datetime.date.today()
    if user is None:
        template_data = MainTemplateData(
            target_date=target_date,
            time_taps=[],
            note_taps=[],
            medication_taps=[],
            workers=fetch_all_workers(),
            previous_period_start=target_date + datetime.timedelta(days=-1),
            next_period_start=target_date + datetime.timedelta(days=1),
            user_email="",
        )
    else:
        user_email = user["email"]

        time_tap_views = fetch_time_taps(worker=user_email, target_date=target_date)
        unused_time_tap_views = get_unused_time_tap_blocks_for_day([tap.name for tap in time_tap_views])
        medication_tap_views = get_medication_views(worker=user_email, date=target_date)
        unused_medication_tap_views = get_unused_medication_tap_blocks_for_day(
            [tap.name for tap in medication_tap_views])
        note_taps = fetch_note_taps(worker=user_email, date=target_date)
        template_data = MainTemplateData(
            target_date=target_date,
            time_taps=time_tap_views + unused_time_tap_views,
            note_taps=note_taps,
            medication_taps=medication_tap_views + unused_medication_tap_views,
            workers=fetch_all_workers(),
            previous_period_start=target_date + datetime.timedelta(days=-1),
            next_period_start=target_date + datetime.timedelta(days=1),
            user_email=user_email,
        )

    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            **template_data.to_dict()
        }
    )


@app.route("/summary")
async def summary_page(request: Request):
    user = request.session.get('user')
    if user is None:
        return HTMLResponse('<a href="/login">Login with Google</a>')
    worker = user["email"]
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
async def post_time_tap(time_tap: TimeTapDto, user_email: str = Depends(get_current_user)):
    time_tap.worker = user_email
    add_time_tap(time_tap, minutes=15)

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.delete("/time_tap")
async def delete_time_tap(time_tap: TimeTapDto, user_email: str = Depends(get_current_user)):
    time_tap.worker = user_email
    tap = fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)
    if tap is not None and tap.duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid input, cannot have negative total time")

    add_time_tap(time_tap, minutes=-15)

    return fetch_time_tap(name=time_tap.name, worker=time_tap.worker, target_date=time_tap.date)


@app.post("/note_tap")
async def post_a_note(note: NoteTapDto, user_email: str = Depends(get_current_user)):
    note.worker = user_email
    return add_note_tap(note)


@app.delete("/note_tap")
async def post_a_note(note: NoteTapDto, user_email: str = Depends(get_current_user)):
    note.worker = user_email
    try:
        delete_note_tap(note)
    except InvalidInputException as e:
        log.warning(e)
        raise HTTPException(status_code=400, detail="Invalid input")


@app.post("/medication_tap")
async def post_time_tap(medication_tap: MedicationTapDto, user_email: str = Depends(get_current_user)):
    medication_tap.worker = user_email

    update_medication_tap(medication_tap, dose_taken=1)

    return get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)[0]


@app.delete("/medication_tap")
async def delete_time_tap(medication_tap: MedicationTapDto, user_email: str = Depends(get_current_user)):
    medication_tap.worker = user_email
    tap = get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)
    if len(tap) == 0 or tap[0].doses <= 0:
        raise HTTPException(status_code=400, detail="Invalid input")

    update_medication_tap(medication_tap, dose_taken=-1)

    return get_medication_views(name=medication_tap.name, worker=medication_tap.worker, date=medication_tap.date)[0]


@app.post("/medication")
async def post_medication(medication: MedicationDto, assure_authenticated: str = Depends(get_current_user)):
    add_medication(medication)


@app.post("/statistics")
async def time_tap_statistics(note: TimeTapStatisticsRequestDto, user_email: str = Depends(get_current_user)):
    note.worker = user_email
    return fetch_time_taps(worker=note.worker, first_date=note.first_date, last_date=note.last_date)


@app.get("/favicon.ico")
async def get_favicon():
    return RedirectResponse("/static/favicon.ico")


@app.route("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    res = await oauth.google.authorize_redirect(request, redirect_uri)
    return res


@app.route("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session["user"] = dict(user)
    return RedirectResponse(url="/")


@app.route('/logout')
async def logout(request: Request, assure_authenticated: str = Depends(get_current_user)):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":  # for debugging
    uvicorn.run(app, host="0.0.0.0", port=8000)
