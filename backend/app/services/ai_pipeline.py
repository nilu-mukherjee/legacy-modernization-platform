"""
AI Pipeline Service
===================

Abstracts AI provider calls (Anthropic Claude / OpenAI) behind a common
interface.  Implements the two-tier strategy:

1. **Bulk file analysis** (cheap model) — per-file semantic debt detection.
2. **Recommendation synthesis** (powerful model) — cross-repo insights.
3. **On-demand refactoring** (powerful model) — code generation.

Provider selection is driven by ``settings.AI_PROVIDER``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings

# ── Prompt Templates ─────────────────────────────────────────────────────────

FILE_ANALYSIS_PROMPT = """You are a senior software architect analyzing code for technical debt.

Analyze the following {language} code and identify:
1. Code smells (with severity: low/medium/high/critical)
2. Anti-patterns
3. Potential bugs
4. Security concerns
5. Deprecated API usage

File: {file_path}
Existing metrics: complexity={complexity}, loc={loc}, nesting={nesting}

Code:
```{language}
{code}
```

Respond in JSON format:
{{"issues": [{{"severity": "...", "title": "...", "description": "...", "suggestion": "..."}}], "opportunities": [{{"title": "...", "description": "..."}}]}}"""

SYNTHESIS_PROMPT = """You are a senior application modernization architect.

Repository: {repo_name}
Languages: {languages}
Total Files: {total_files}, LOC: {total_loc}

Quantitative analysis results:
{metrics_summary}

Top file-level issues:
{top_issues}

Dependency findings:
{dependency_summary}

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

Respond in JSON:
{{"executive_summary": "...", "recommendations": [...]}}"""

REFACTOR_PROMPT = """You are a senior software engineer performing a code refactoring.

Context:
- Recommendation: {recommendation_title}
- Rationale: {rationale}
- Language: {language}
- File: {file_path}

Original code:
```{language}
{code}
```

Refactor this code to address the recommendation. Rules:
1. Preserve all existing functionality
2. Maintain the same API/interface
3. Follow {language} best practices and modern idioms
4. Add appropriate comments explaining changes
5. Keep the refactored code production-ready

Return ONLY the refactored code, no explanations."""


# ── Abstract Base ────────────────────────────────────────────────────────────


class AIProvider(ABC):
    """Abstract base for AI provider integrations."""

    @abstractmethod
    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        """Send a prompt and return the text response."""
        ...

    @abstractmethod
    async def complete_json(self, prompt: str, *, model: str | None = None) -> dict:
        """Send a prompt and parse the response as JSON."""
        ...


# ── Anthropic Provider ───────────────────────────────────────────────────────


class AnthropicProvider(AIProvider):
    """Anthropic Claude integration."""

    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        response = await self._client.messages.create(
            model=model or settings.AI_MODEL_POWERFUL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def complete_json(self, prompt: str, *, model: str | None = None) -> dict:
        text = await self.complete(prompt, model=model)
        # Strip markdown code fences if present.
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

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        response = await self._client.chat.completions.create(
            model=model or settings.AI_MODEL_POWERFUL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, prompt: str, *, model: str | None = None) -> dict:
        text = await self.complete(prompt, model=model)
        text = text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        return json.loads(text.strip())


# ── Factory ──────────────────────────────────────────────────────────────────


def get_ai_provider() -> AIProvider:
    """
    Create the AI provider based on ``settings.AI_PROVIDER``.

    Returns:
        An :class:`AnthropicProvider` or :class:`OpenAIProvider`.
    """
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
    """
    Analyse a single file with the **fast** (cheap) AI model.

    Returns parsed JSON with ``issues`` and ``opportunities``.
    """
    provider = provider or get_ai_provider()
    prompt = FILE_ANALYSIS_PROMPT.format(
        language=language,
        file_path=file_path,
        complexity=complexity,
        loc=loc,
        nesting=nesting,
        code=code[:16000],  # Truncate to avoid token limits.
    )
    try:
        return await provider.complete_json(prompt, model=settings.AI_MODEL_FAST)
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
    """
    Synthesise cross-repo recommendations with the **powerful** model.

    Returns parsed JSON with ``executive_summary`` and ``recommendations``.
    """
    provider = provider or get_ai_provider()
    prompt = SYNTHESIS_PROMPT.format(
        repo_name=repo_name,
        languages=json.dumps(languages),
        total_files=total_files,
        total_loc=total_loc,
        metrics_summary=metrics_summary,
        top_issues=top_issues,
        dependency_summary=dependency_summary,
    )
    try:
        return await provider.complete_json(prompt, model=settings.AI_MODEL_POWERFUL)
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
    """
    Generate refactored code on demand with the **powerful** model.

    Returns the refactored code as a string.
    """
    provider = provider or get_ai_provider()
    prompt = REFACTOR_PROMPT.format(
        recommendation_title=recommendation_title,
        rationale=rationale,
        language=language,
        file_path=file_path,
        code=code[:16000],
    )
    return await provider.complete(prompt, model=settings.AI_MODEL_POWERFUL)
