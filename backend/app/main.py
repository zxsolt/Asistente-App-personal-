from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import Base, engine
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create all tables on startup (dev convenience; use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_sqlite_task_time_columns()
    yield


app = FastAPI(
    title="Weekly Planner API",
    version="1.0.0",
    description="Personal weekly task planner — plan, track, review.",
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


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
