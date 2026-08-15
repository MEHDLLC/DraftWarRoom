from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from .database import run_migrations
from .routers import league, players, lineup, matchups, waivers, trades, schedule, chat, notifications, draft, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await run_migrations()

    # Start scheduler in non-test environments
    from .config import get_settings
    settings = get_settings()
    if settings.app_env != "test":
        from .jobs.scheduler import start_scheduler
        start_scheduler()

    yield
    # Shutdown
    if settings.app_env != "test":
        from .jobs.scheduler import shutdown_scheduler
        shutdown_scheduler()


app = FastAPI(
    title="DraftWarRoom",
    description="Fantasy Football Season-Long Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(league.router, prefix="/api/v1/league", tags=["league"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(lineup.router, prefix="/api/v1/lineup", tags=["lineup"])
app.include_router(matchups.router, prefix="/api/v1/matchups", tags=["matchups"])
app.include_router(waivers.router, prefix="/api/v1/waivers", tags=["waivers"])
app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["schedule"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(draft.router, prefix="/api/v1/draft", tags=["draft"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "app": "DraftWarRoom"}


# Serve React static files in production
static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
