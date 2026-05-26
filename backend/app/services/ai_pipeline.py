"""
AI Pipeline Service
===================

Abstracts AI provider calls (Anthropic Claude / OpenAI) behind a common
interface.  Implements the two-tier strategy:

1. **Bulk file analysis** (cheap model) — per-file semantic debt detection.
2. **Recommendation synthesis** (powerful model) — cross-repo insights.
3. **On-demand refactoring** (powerful model) — code generation.

Provider selection is driven by ``settings.AI_PROVIDER``.

Prompt caching
--------------
For the Anthropic provider every call separates the static instruction text
(system) from the dynamic data (user message).  The system block is marked
with ``cache_control: {type: ephemeral}`` so Claude caches it for up to
5 minutes across repeated calls, cutting both latency and cost significantly
during bulk file analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


async def _retry_with_backoff(
    coro_fn: Callable[[], Awaitable[_T]],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    label: str = "ai_call",
) -> _T:
    """Retry an async call with exponential backoff on transient API errors.

    Catches Anthropic / OpenAI overload (529), service-unavailable (503),
    timeouts, connection errors, and rate-limit errors.  Re-raises everything
    else immediately.
    """
    attempt = 0
    while True:
        try:
            return await coro_fn()
        except Exception as exc:  # noqa: BLE001
            transient = _is_transient_error(exc)
            attempt += 1
            if not transient or attempt > max_retries:
                logger.warning("%s failed (attempt %d): %s", label, attempt, exc)
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logger.info(
                "%s transient error on attempt %d (%s); retrying in %.1fs",
                label, attempt, type(exc).__name__, delay,
            )
            await asyncio.sleep(delay)


def _is_transient_error(exc: BaseException) -> bool:
    """Best-effort detection of retryable LLM API errors."""
    name = type(exc).__name__
    if name in {
        "APIConnectionError", "APIStatusError", "APITimeoutError",
        "RateLimitError", "InternalServerError",
    }:
        return True
    status_code = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    if isinstance(status_code, int) and status_code in {408, 429, 500, 502, 503, 504, 529}:
        return True
    if isinstance(exc, (asyncio.TimeoutError, ConnectionError)):
        return True
    return False

# ── Prompt Templates ─────────────────────────────────────────────────────────
# Each prompt is split into a SYSTEM part (static, cacheable) and a USER part
# (dynamic, injected per call).  Only the Anthropic provider uses this split
# for caching; the OpenAI provider treats the system part as a system message.

# -- File analysis ------------------------------------------------------------

FILE_ANALYSIS_SYSTEM = """You are a senior software architect analyzing code for technical debt.

Analyze the code provided by the user and identify:
1. Code smells (with severity: low/medium/high/critical)
2. Anti-patterns
3. Potential bugs
4. Security concerns
5. Deprecated API usage

Respond in JSON format:
{"issues": [{"severity": "...", "title": "...", "description": "...", "suggestion": "..."}], "opportunities": [{"title": "...", "description": "..."}]}"""

FILE_ANALYSIS_USER = """File: {file_path}
Language: {language}
Metrics: complexity={complexity}, loc={loc}, nesting={nesting}

Code:
```{language}
{code}
```"""

# -- Synthesis ----------------------------------------------------------------

SYNTHESIS_SYSTEM = """You are a senior application modernization architect.

Generate a comprehensive modernization plan with:
1. Executive summary (2-3 sentences)
2. Top 10 prioritized recommendations with category, effort estimate (hours), and impact score (1-10)
3. Quick wins (< 4 hours effort)
4. Strategic improvements (> 1 week effort)

For each recommendation provide:
- category: one of [upgrade, refactor, security, performance, testing, architecture]
- priority: one of [critical, high, medium, low]
- title: concise action item
- description: what and why
- rationale: business impact
- implementation_steps: numbered steps
- estimated_hours: realistic estimate
- impact_score: 1-10
- affected_files: list of relative file paths from repo root that need changes, inferred from the issues above (empty list if unknown)

Respond in JSON:
{"executive_summary": "...", "recommendations": [...]}"""

SYNTHESIS_USER = """Repository: {repo_name}
Languages: {languages}
Total Files: {total_files}, LOC: {total_loc}

Quantitative analysis results:
{metrics_summary}

Top file-level issues:
{top_issues}

Dependency findings:
{dependency_summary}"""

# -- Refactoring --------------------------------------------------------------

REFACTOR_SYSTEM = """You are a senior software engineer performing a code refactoring.

Rules:
1. Preserve all existing functionality
2. Maintain the same API/interface
3. Follow the target language's best practices and modern idioms
4. Add appropriate comments explaining changes
5. Keep the refactored code production-ready

Return ONLY the refactored code, no explanations."""

REFACTOR_USER = """Recommendation: {recommendation_title}
Rationale: {rationale}
Language: {language}
File: {file_path}

Original code:
```{language}
{code}
```"""

# Legacy single-string constants kept for any external callers.
FILE_ANALYSIS_PROMPT = FILE_ANALYSIS_SYSTEM + "\n\n" + FILE_ANALYSIS_USER
SYNTHESIS_PROMPT = SYNTHESIS_SYSTEM + "\n\n" + SYNTHESIS_USER
REFACTOR_PROMPT = REFACTOR_SYSTEM + "\n\n" + REFACTOR_USER


# ── Abstract Base ────────────────────────────────────────────────────────────


class AIProvider(ABC):
    """Abstract base for AI provider integrations."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> str:
        """Send a prompt and return the text response.

        Args:
            prompt: The user-turn message.
            system: Optional static system instruction (cached on Anthropic).
            model: Override the default model.
        """
        ...

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> dict:
        """Send a prompt and parse the response as JSON."""
        ...


# ── Anthropic Provider ───────────────────────────────────────────────────────


class AnthropicProvider(AIProvider):
    """Anthropic Claude integration with prompt caching on system blocks."""

    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": model or settings.AI_MODEL_POWERFUL,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        response = await _retry_with_backoff(
            lambda: self._client.messages.create(**kwargs),
            label="anthropic.messages.create",
        )
        return response.content[0].text

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> dict:
        text = await self.complete(prompt, system=system, model=model)
        text = text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        return json.loads(text.strip())


# ── OpenAI Provider ──────────────────────────────────────────────────────────


class OpenAIProvider(AIProvider):
    """OpenAI GPT integration."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await _retry_with_backoff(
            lambda: self._client.chat.completions.create(
                model=model or settings.AI_MODEL_POWERFUL,
                messages=messages,
                max_tokens=4096,
            ),
            label="openai.chat.completions.create",
        )
        return response.choices[0].message.content or ""

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
    ) -> dict:
        text = await self.complete(prompt, system=system, model=model)
        text = text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        return json.loads(text.strip())


# ── Factory ──────────────────────────────────────────────────────────────────


def get_ai_provider() -> AIProvider:
    """Create the AI provider based on ``settings.AI_PROVIDER``."""
    if settings.AI_PROVIDER == "openai":
        return OpenAIProvider()
    return AnthropicProvider()


# ── High-level Pipeline Functions ────────────────────────────────────────────


async def analyze_file_with_ai(
    file_path: str,
    code: str,
    language: str,
    complexity: int,
    loc: int,
    nesting: int,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Analyse a single file with the **fast** (cheap) AI model.

    The static system prompt is cached on Anthropic — only the dynamic
    file metrics + code are sent uncached on repeat calls.

    Returns parsed JSON with ``issues`` and ``opportunities``.
    """
    provider = provider or get_ai_provider()
    user_prompt = FILE_ANALYSIS_USER.format(
        language=language,
        file_path=file_path,
        complexity=complexity,
        loc=loc,
        nesting=nesting,
        code=code[:16000],
    )
    try:
        return await provider.complete_json(
            user_prompt,
            system=FILE_ANALYSIS_SYSTEM,
            model=settings.AI_MODEL_FAST,
        )
    except Exception:
        return {"issues": [], "opportunities": []}


async def generate_recommendations(
    repo_name: str,
    languages: dict,
    total_files: int,
    total_loc: int,
    metrics_summary: str,
    top_issues: str,
    dependency_summary: str,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Synthesise cross-repo recommendations with the **powerful** model.

    Returns parsed JSON with ``executive_summary`` and ``recommendations``.
    """
    provider = provider or get_ai_provider()
    user_prompt = SYNTHESIS_USER.format(
        repo_name=repo_name,
        languages=json.dumps(languages),
        total_files=total_files,
        total_loc=total_loc,
        metrics_summary=metrics_summary,
        top_issues=top_issues,
        dependency_summary=dependency_summary,
    )
    try:
        return await provider.complete_json(
            user_prompt,
            system=SYNTHESIS_SYSTEM,
            model=settings.AI_MODEL_POWERFUL,
        )
    except Exception:
        return {"executive_summary": "AI analysis unavailable.", "recommendations": []}


async def generate_refactoring(
    code: str,
    recommendation_title: str,
    rationale: str,
    language: str,
    file_path: str,
    provider: AIProvider | None = None,
) -> str:
    """Generate refactored code on demand with the **powerful** model.

    Returns the refactored code as a string.
    """
    provider = provider or get_ai_provider()
    user_prompt = REFACTOR_USER.format(
        recommendation_title=recommendation_title,
        rationale=rationale,
        language=language,
        file_path=file_path,
        code=code[:16000],
    )
    return await provider.complete(
        user_prompt,
        system=REFACTOR_SYSTEM,
        model=settings.AI_MODEL_POWERFUL,
    )
