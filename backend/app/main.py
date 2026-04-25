import asyncio
from contextlib import asynccontextmanager, suppress
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.assistant.proactive_watcher import ProactiveWatcher
from app.models.user import User
from app.assistant import router as assistant_router
from app.notes import router as notes_router
from app.reminders import router as reminders_router
from app.telegram import router as telegram_router
from app.routers import auth, weeks, pool_tasks, full_tasks, actions, distribution, review, pomodoro_presets


async def _ensure_sqlite_task_time_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(full_tasks)"))
        columns = {row[1] for row in result.fetchall()}

        if "time_budget_minutes" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN time_budget_minutes INTEGER"))
        if "time_spent_seconds" not in columns:
            await conn.execute(
                text("ALTER TABLE full_tasks ADD COLUMN time_spent_seconds INTEGER NOT NULL DEFAULT 0")
            )
        if "limit_mode" not in columns:
            await conn.execute(
                text("ALTER TABLE full_tasks ADD COLUMN limit_mode VARCHAR(10) NOT NULL DEFAULT 'warn'")
            )
        if "priority" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN priority VARCHAR(10)"))
        if "due_at" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN due_at DATETIME"))
        if "source" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN source VARCHAR(32)"))
        if "source_ref" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN source_ref VARCHAR(255)"))
        if "natural_language_input" not in columns:
            await conn.execute(text("ALTER TABLE full_tasks ADD COLUMN natural_language_input TEXT"))


async def _ensure_sqlite_user_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = {row[1] for row in result.fetchall()}

        if "is_superuser" not in columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT 0"))


async def _ensure_bootstrap_admin() -> None:
    if not settings.ENSURE_BOOTSTRAP_ADMIN:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == settings.BOOTSTRAP_ADMIN_USERNAME)
        )
        user = result.scalar_one_or_none()

        if user is None:
            session.add(
                User(
                    username=settings.BOOTSTRAP_ADMIN_USERNAME,
                    email=settings.BOOTSTRAP_ADMIN_EMAIL,
                    hashed_password=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
                    is_superuser=True,
                )
            )
        else:
            user.email = settings.BOOTSTRAP_ADMIN_EMAIL
            user.hashed_password = hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
            user.is_superuser = True

        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    watcher_task: asyncio.Task | None = None
    watcher: ProactiveWatcher | None = None
    # Create all tables on startup (dev convenience; use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_sqlite_task_time_columns()
    await _ensure_sqlite_user_columns()
    await _ensure_bootstrap_admin()
    if settings.ASSISTANT_WATCHER_ENABLED:
        watcher = ProactiveWatcher()
        watcher_task = asyncio.create_task(watcher.run_forever())
    try:
        yield
    finally:
        if watcher:
            watcher.stop()
        if watcher_task:
            watcher_task.cancel()
            with suppress(asyncio.CancelledError):
                await watcher_task


app = FastAPI(
    title="Weekly Planner API",
    version="1.0.0",
    description="Personal weekly task planner - plan, track, review.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(weeks.router)
app.include_router(pool_tasks.router)
app.include_router(full_tasks.router)
app.include_router(actions.router)
app.include_router(distribution.router)
app.include_router(review.router)
app.include_router(pomodoro_presets.router)
app.include_router(notes_router)
app.include_router(reminders_router)
app.include_router(assistant_router)
app.include_router(telegram_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
