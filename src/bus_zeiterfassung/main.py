from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from bus_zeiterfassung.auth import NotAuthenticated
from bus_zeiterfassung.config import settings
from bus_zeiterfassung.db import init_db
from bus_zeiterfassung.routes import entries, export, pages

_HERE = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters — set it in .env")
    init_db()
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="bus-zeiterfassung", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="bzsession",
    max_age=60 * 60 * 24 * 30,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")

app.include_router(pages.router)
app.include_router(entries.router)
app.include_router(export.router)


@app.exception_handler(NotAuthenticated)
async def _redirect_to_login(request: Request, exc: NotAuthenticated) -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)
