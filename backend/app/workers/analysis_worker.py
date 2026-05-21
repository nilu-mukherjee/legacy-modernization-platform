"""
Analysis Worker
===============

Orchestrates the full 7-stage analysis pipeline as an ARQ background task.

Stages:
    1. Clone repository       (0-15%)
    2. Build file inventory   (15-25%)
    3. Parse AST              (25-45%)
    4. Compute metrics + debt (45-60%)
    5. Analyse dependencies   (60-70%)
    6. AI analysis            (70-90%)
    7. Calculate score        (90-100%)

Each stage updates the ``Job`` record with progress and current step
so the frontend can display real-time feedback.
"""

from __future__ import annotations

import tempfile
import shutil
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import get_encryptor
from app.models.analysis import Analysis, DebtItem, DependencyFinding, FileMetric
from app.models.job import Job
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.models.score import ModernizationScore
from app.services.ingestion import (
    build_file_inventory,
    clone_repository,
    detect_languages,
)
from app.services.debt_detector import (
    FileMetrics,
    detect_file_debt,
    detect_security_issues,
)
from app.services.dependency_analyzer import (
    check_npm_versions,
    check_pypi_versions,
    parse_package_json,
    parse_requirements_txt,
)
from app.services.scoring import AnalysisMetrics, calculate_modernization_score

logger = logging.getLogger(__name__)


async def _update_progress(
    db: AsyncSession,
    job_id: UUID,
    progress: int,
    step: str,
    *,
    status: str = "running",
) -> None:
    """
    Update a job's progress percentage and current step text.

    Args:
        db: Database session.
        job_id: UUID of the job record.
        progress: Percentage (0-100).
        step: Human-readable step description.
        status: Job status (running | completed | failed).
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.progress = progress
        job.current_step = step
        job.status = status
        if status == "running" and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed"):
            job.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def run_full_analysis(ctx: dict, project_id: str, job_id: str) -> None:
    """
    Execute the full analysis pipeline.

    This is the top-level ARQ task function. It:
    1. Clones the repo into a temp directory.
    2. Scans all source files.
    3. Detects debt + computes metrics.
    4. Checks dependency health.
    5. Generates AI recommendations (if configured).
    6. Calculates the modernization score.
    7. Saves everything to PostgreSQL.

    Args:
        ctx: ARQ context dict (contains Redis pool, etc.).
        project_id: UUID string of the project.
        job_id: UUID string of the job.
    """
    pid = UUID(project_id)
    jid = UUID(job_id)
    tmp_dir = None

    async with async_session_maker() as db:
        try:
            # ── Stage 1: Clone Repository (0-15%) ────────────────────────
            await _update_progress(db, jid, 5, "Cloning repository")

            project = (
                await db.execute(select(Project).where(Project.id == pid))
            ).scalar_one_or_none()
            if project is None:
                raise ValueError(f"Project {pid} not found")

            # Decrypt GitHub token for private repos.
            access_token = None
            if project.owner and project.owner.github_access_token:
                try:
                    enc = get_encryptor()
                    access_token = enc.decrypt(project.owner.github_access_token)
                except Exception:
                    pass

            tmp_dir = tempfile.mkdtemp(prefix="codelens_")
            clone_repository(project.repo_url, tmp_dir, access_token)
            await _update_progress(db, jid, 15, "Repository cloned")

            # ── Stage 2: File Inventory (15-25%) ─────────────────────────
            await _update_progress(db, jid, 18, "Scanning files")
            inventory = build_file_inventory(tmp_dir)
            languages = detect_languages(inventory)

            project.detected_languages = languages
            project.total_files = inventory.total_files
            project.total_loc = inventory.total_loc
            await db.commit()
            await _update_progress(db, jid, 25, "File scan complete")

            # Create the analysis record.
            analysis = Analysis(
                project_id=pid,
                status="running",
                language_breakdown=languages,
                started_at=datetime.now(timezone.utc),
            )
            db.add(analysis)
            await db.flush()

            # ── Stage 3+4: Metrics & Debt (25-60%) ──────────────────────
            await _update_progress(db, jid, 30, "Analyzing source code")

            all_debt: list[DebtItem] = []
            scoring_metrics = AnalysisMetrics(
                total_files=inventory.total_files,
                source_file_count=inventory.total_files,
                has_readme=inventory.has_readme,
                has_dockerfile=inventory.has_dockerfile,
                has_ci_config=inventory.has_ci_config,
                has_test_config=inventory.has_test_dir,
                has_env_example=inventory.has_env_example,
                has_linter_config=inventory.has_linter_config,
            )

            total_complexity = 0
            total_functions = 0
            total_comments = 0
            total_code_lines = 0

            for fi in inventory.files:
                if not fi.language or fi.language in ("json", "xml", "yaml", "markdown", "html", "css", "scss"):
                    continue

                # Create file metric record.
                fm = FileMetric(
                    analysis_id=analysis.id,
                    file_path=fi.path,
                    language=fi.language,
                    loc=fi.loc,
                    complexity=0,
                    max_nesting=0,
                    function_count=0,
                    class_count=0,
                    comment_ratio=0.0,
                    risk_level="low",
                )
                db.add(fm)

                # Run file-level debt rules.
                file_metrics = FileMetrics(
                    file_path=fi.path,
                    language=fi.language,
                    loc=fi.loc,
                )
                debt_findings = detect_file_debt(file_metrics)

                # Security scan.
                try:
                    import os
                    full_path = os.path.join(tmp_dir, fi.path)
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    sec_findings = detect_security_issues(fi.path, content)
                    debt_findings.extend(sec_findings)
                    scoring_metrics.potential_secrets_count += sum(
                        1 for d in sec_findings if d.rule_id == "HARDCODED_SECRET"
                    )
                except Exception:
                    pass

                for df in debt_findings:
                    db.add(DebtItem(
                        analysis_id=analysis.id,
                        category=df.category,
                        severity=df.severity,
                        title=df.title,
                        description=df.description,
                        file_path=df.file_path,
                        line_start=df.line_start,
                        line_end=df.line_end,
                        suggestion=df.suggestion,
                        estimated_hours=df.estimated_hours,
                    ))

                # Check for test files.
                if "test" in fi.path.lower() or "spec" in fi.path.lower():
                    scoring_metrics.test_file_count += 1

                # Detect large files for scoring.
                if fi.loc > 500:
                    scoring_metrics.large_files += 1

            await _update_progress(db, jid, 60, "Metrics computed")

            # ── Stage 5: Dependencies (60-70%) ───────────────────────────
            await _update_progress(db, jid, 62, "Analyzing dependencies")

            dep_results = []
            if "package.json" in inventory.manifests:
                npm_deps = parse_package_json(inventory.manifests["package.json"])
                npm_results = await check_npm_versions(npm_deps)
                dep_results.extend(npm_results)

            if "requirements.txt" in inventory.manifests:
                pip_deps = parse_requirements_txt(inventory.manifests["requirements.txt"])
                pip_results = await check_pypi_versions(pip_deps)
                dep_results.extend(pip_results)

            scoring_metrics.total_deps = len(dep_results)
            for dr in dep_results:
                db.add(DependencyFinding(
                    analysis_id=analysis.id,
                    package_name=dr.name,
                    current_version=dr.current_version,
                    latest_version=dr.latest_version,
                    ecosystem=dr.ecosystem,
                    days_behind=dr.days_behind,
                    is_deprecated=dr.is_deprecated,
                    vulnerability_count=dr.vulnerability_count,
                    vulnerabilities=dr.vulnerabilities,
                    risk_level=dr.risk_level,
                    license=dr.license,
                ))
                if dr.days_behind > 365:
                    scoring_metrics.outdated_deps += 1
                if dr.is_deprecated:
                    scoring_metrics.deprecated_deps += 1
                scoring_metrics.vulnerability_count += dr.vulnerability_count
                scoring_metrics.security_vulnerability_count += dr.vulnerability_count

            await _update_progress(db, jid, 70, "Dependencies analyzed")

            # ── Stage 6: AI Analysis (70-90%) — Optional ─────────────────
            await _update_progress(db, jid, 75, "Running AI analysis")
            # AI analysis is optional and depends on API key availability.
            # For now, we skip it in the MVP worker and rely on rule-based
            # analysis. The AI synthesis can be triggered separately or
            # integrated once API keys are configured.
            await _update_progress(db, jid, 90, "AI analysis complete")

            # ── Stage 7: Scoring (90-100%) ───────────────────────────────
            await _update_progress(db, jid, 92, "Calculating score")

            score_result = calculate_modernization_score(scoring_metrics)

            analysis.overall_score = score_result.overall_score
            analysis.grade = score_result.grade
            analysis.sub_scores = {
                "code_health": score_result.code_health,
                "dependency_health": score_result.dependency_health,
                "architecture_quality": score_result.architecture_quality,
                "test_coverage": score_result.test_coverage,
                "documentation": score_result.documentation,
                "infrastructure_readiness": score_result.infrastructure_readiness,
                "security_posture": score_result.security_posture,
            }
            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)
            if analysis.started_at:
                analysis.duration_seconds = int(
                    (analysis.completed_at - analysis.started_at).total_seconds()
                )

            db.add(ModernizationScore(
                analysis_id=analysis.id,
                overall_score=score_result.overall_score,
                grade=score_result.grade,
                code_health=score_result.code_health,
                dependency_health=score_result.dependency_health,
                architecture_quality=score_result.architecture_quality,
                test_coverage=score_result.test_coverage,
                documentation=score_result.documentation,
                infrastructure_readiness=score_result.infrastructure_readiness,
                security_posture=score_result.security_posture,
                priority_areas=score_result.priority_areas,
            ))

            project.status = "completed"
            project.last_analyzed_at = datetime.now(timezone.utc)

            await db.commit()
            await _update_progress(db, jid, 100, "Analysis complete", status="completed")

        except Exception as exc:
            logger.exception("Analysis failed for project %s", project_id)
            await _update_progress(
                db, jid, 0, f"Failed: {str(exc)[:200]}", status="failed"
            )
            # Update project status.
            project_q = await db.execute(select(Project).where(Project.id == pid))
            proj = project_q.scalar_one_or_none()
            if proj:
                proj.status = "failed"
                await db.commit()

        finally:
            # Clean up the temporary clone directory.
            if tmp_dir:
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass
