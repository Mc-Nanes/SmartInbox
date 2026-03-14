from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.analysis import router as analysis_router
from app.core.config import get_settings

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()

app = FastAPI(title=settings.app_name, description=settings.app_description)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(analysis_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
