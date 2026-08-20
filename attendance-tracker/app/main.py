"""FastAPI application entry point."""
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine, SessionLocal
from .deps import get_current_user
from .security import decode_access_token
from .routers import activity_logs, announcements, attendance, auth, breaks, chat, departments, holidays, leaves, meetings, notifications, overtime, people, profile, reports, salary, settings as settings_router, shift_swaps, shifts, tasks, users

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Simple auto-create on startup. For production, use Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Attendance tracking system built with FastAPI + PostgreSQL.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/api/auth/login", "/docs", "/openapi.json", "/redoc", "/health"}
    SKIP_METHODS = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next):
        if request.method in self.SKIP_METHODS or not request.url.path.startswith("/api/"):
            return await call_next(request)
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        body_bytes = None
        try:
            body_bytes = await request.body()
        except Exception:
            pass

        response = await call_next(request)

        try:
            body = None
            if body_bytes:
                try:
                    body = json.loads(body_bytes)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    body = None

            parts = request.url.path.strip("/").split("/")
            entity = parts[1] if len(parts) > 1 else "unknown"
            entity_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None

            action_map = {"POST": "create", "PATCH": "update", "PUT": "update", "DELETE": "delete"}
            action = action_map.get(request.method, request.method.lower())

            token = request.headers.get("authorization", "").replace("Bearer ", "")
            user_id, username = None, None
            if token:
                try:
                    payload = decode_access_token(token)
                    if payload:
                        user_id = int(payload.get("sub", 0)) or None
                        username = payload.get("role", "")
                except Exception:
                    pass

            details = None
            if body and isinstance(body, dict):
                safe = {k: v for k, v in body.items() if k not in ("password", "hashed_password", "new_password", "current_password")}
                if safe:
                    details = safe

            async with SessionLocal() as db:
                from .audit import log_activity
                await log_activity(
                    db, user_id=user_id, username=username,
                    action=action, entity=entity, entity_id=entity_id,
                    details=details, ip_address=request.client.host if request.client else None,
                )
                await db.commit()
        except Exception:
            pass

        return response


app.add_middleware(AuditMiddleware)

app.include_router(auth.router)
app.include_router(people.router)
app.include_router(users.router)
app.include_router(attendance.router)
app.include_router(reports.router)
app.include_router(holidays.router)
app.include_router(shifts.router)
app.include_router(notifications.router)
app.include_router(leaves.router)
app.include_router(breaks.router)
app.include_router(departments.router)
app.include_router(announcements.router)
app.include_router(salary.router)
app.include_router(settings_router.router)
app.include_router(profile.router)
app.include_router(overtime.router)
app.include_router(shift_swaps.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(meetings.router)
app.include_router(activity_logs.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login", include_in_schema=False)
async def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
