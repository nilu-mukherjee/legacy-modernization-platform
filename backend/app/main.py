# Copyright (c) 2026 Nilu Mukherjee.
# Licensed under AGPL-3.0. See LICENSE at repo root.

"""
FastAPI Application Factory
============================

Creates and configures the FastAPI application with middleware, routes,
lifespan events, and the health-check endpoint.

Run in development::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.redis import close_arq, close_redis, init_arq, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Runs startup logic (Redis pool initialisation) before the app begins
    serving requests, and shutdown logic (pool closure) when it stops.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    await init_redis()
    await init_arq()
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────
    await close_arq()
    await close_redis()


# ── App Creation ─────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-Powered Legacy Modernization Platform — analyse repositories, "
        "detect technical debt, and generate modernization recommendations."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

# ── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(v1_router)


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns basic status info. Used by load balancers and uptime monitors.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
