"""
GitHub Webhook Route
====================

POST /api/v1/webhooks/github — receives pull_request events.

When a PR on a ``codelens/fix-*`` branch is merged, the corresponding
recommendation is deleted from the database so it no longer appears in
the frontend.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.recommendation import Recommendation

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        return True  # not configured — skip verification
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@router.post("/webhooks/github", status_code=204)
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Handle GitHub webhook events. Deletes a recommendation when its fix PR is merged."""
    payload_bytes = await request.body()

    if not _verify_signature(payload_bytes, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if request.headers.get("X-GitHub-Event") != "pull_request":
        return

    try:
        body = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if body.get("action") != "closed" or not body.get("pull_request", {}).get("merged"):
        return

    branch: str = body.get("pull_request", {}).get("head", {}).get("ref", "")
    match = re.match(r"^codelens/fix-([0-9a-f]{8})$", branch)
    if not match:
        return

    short_id = match.group(1)

    result = await db.execute(
        select(Recommendation).where(
            func.replace(cast(Recommendation.id, String), "-", "").like(f"{short_id}%")
        )
    )
    rec = result.scalar_one_or_none()
    if rec:
        await db.delete(rec)
        await db.commit()
        logger.info("Recommendation %s deleted after PR merge on branch %s", rec.id, branch)
