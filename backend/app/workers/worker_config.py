"""
ARQ Worker Configuration
========================

Defines the :class:`WorkerSettings` class consumed by the ``arq`` CLI.

Start the worker with::

    arq app.workers.worker_config.WorkerSettings
"""

from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.analysis_worker import run_full_analysis


class WorkerSettings:
    """
    ARQ worker settings.

    ARQ reads this class to discover which task functions to register,
    how to connect to Redis, and queue-level configuration.
    """

    # Task functions registered with this worker.
    functions = [run_full_analysis]

    # Redis connection for the job queue.
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    # Concurrency & timeout settings.
    max_jobs = 3                    # Max parallel analysis jobs.
    job_timeout = 600               # 10 minutes per job.
    max_tries = 2                   # Retry once on transient failures.
    health_check_interval = 30      # Seconds between health pings.
    allow_abort_jobs = True         # Allow manual job cancellation.
