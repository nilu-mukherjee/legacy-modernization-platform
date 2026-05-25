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
from sqlalchemy.orm import selectinload

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
from app.services.ast_parser import parse_file
from app.services.debt_detector import (
    detect_bug_risk_issues,
    detect_class_debt,
    detect_code_style_issues,
    detect_file_debt,
    detect_function_debt,
    detect_security_issues,
)
from app.services.dependency_analyzer import (
    check_npm_versions,
    check_pypi_versions,
    parse_package_json,
    parse_requirements_txt,
)
from app.services.scoring import AnalysisMetrics, calculate_modernization_score
from app.services.ai_pipeline import generate_recommendations, get_ai_provider

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
                await db.execute(
                    select(Project)
                    .where(Project.id == pid)
                    .options(selectinload(Project.owner))
                )
            ).scalar_one_or_none()
            if project is None:
                raise ValueError(f"Project {pid} not found")

            # Decrypt GitHub token for private repos.
            access_token = None
            if project.owner and project.owner.github_access_token:
                try:
                    enc = get_encryptor()
                    access_token = enc.decrypt(project.owner.github_access_token)
                except Exception as exc:
                    logger.warning("Failed to decrypt GitHub token for project %s, cloning as public: %s", pid, exc)

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

            import os

            for fi in inventory.files:
                if not fi.language or fi.language in ("json", "xml", "yaml", "markdown", "html", "css", "scss"):
                    continue

                # Read source content once — used by both AST parser and security scan.
                file_content = ""
                try:
                    full_path = os.path.join(tmp_dir, fi.path)
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                        file_content = fh.read()
                except Exception as exc:
                    logger.warning("Could not read file %s, skipping AST parse: %s", fi.path, exc)

                # AST parse — returns real complexity / nesting / function counts.
                parse_result = parse_file(fi.path, file_content, fi.language)
                fm_data = parse_result.file_metrics

                risk_level = "low"
                if fm_data.max_complexity > 20 or fm_data.max_nesting > 6:
                    risk_level = "high"
                elif fm_data.max_complexity > 10 or fm_data.max_nesting > 4:
                    risk_level = "medium"

                fm = FileMetric(
                    analysis_id=analysis.id,
                    file_path=fi.path,
                    language=fi.language,
                    loc=fi.loc,
                    complexity=fm_data.max_complexity,
                    max_nesting=fm_data.max_nesting,
                    function_count=fm_data.function_count,
                    class_count=fm_data.class_count,
                    comment_ratio=fm_data.comment_ratio,
                    risk_level=risk_level,
                )
                db.add(fm)

                # Accumulate scoring metrics.
                total_complexity += fm_data.max_complexity
                total_functions += fm_data.function_count
                total_comments += int(fm_data.comment_ratio * fi.loc)
                total_code_lines += fi.loc

                # File-level debt rules.
                debt_findings = detect_file_debt(fm_data)

                # Function-level debt rules.
                for func in parse_result.functions:
                    debt_findings.extend(detect_function_debt(func))
                    if func.loc > 60:
                        scoring_metrics.long_methods += 1

                # Class-level debt rules.
                for cls in parse_result.classes:
                    debt_findings.extend(detect_class_debt(cls))

                # Security, bug risk, and code style scans.
                if file_content:
                    sec_findings = detect_security_issues(fi.path, file_content)
                    debt_findings.extend(sec_findings)
                    scoring_metrics.potential_secrets_count += sum(
                        1 for d in sec_findings if d.rule_id == "HARDCODED_SECRET"
                    )
                    debt_findings.extend(detect_bug_risk_issues(fi.path, file_content))
                    debt_findings.extend(detect_code_style_issues(fi.path, file_content))

                all_debt.extend(debt_findings)
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

            # Update aggregate scoring metrics.
            if total_functions > 0:
                scoring_metrics.avg_cyclomatic_complexity = total_complexity / total_functions
                scoring_metrics.total_methods = total_functions
            if total_code_lines > 0:
                scoring_metrics.overall_comment_ratio = total_comments / total_code_lines
            scoring_metrics.avg_imports_per_file = (
                sum(getattr(f, "import_count", 0) for f in inventory.files) / max(inventory.total_files, 1)
            )

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

            # ── Stage 6: AI Analysis (70-90%) ────────────────────────────
            await _update_progress(db, jid, 75, "Running AI analysis")
            try:
                # Build context summaries for the synthesis prompt.
                top_debt = sorted(all_debt, key=lambda d: (
                    {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(d.severity, 4)
                ))[:20]
                top_issues_text = "\n".join(
                    f"- [{d.severity}] {d.title} ({d.file_path})"
                    for d in top_debt
                ) or "No issues detected"

                dep_text = (
                    f"{len(dep_results)} dependencies; "
                    f"{sum(1 for d in dep_results if d.days_behind > 180)} outdated; "
                    f"{sum(1 for d in dep_results if d.vulnerability_count > 0)} vulnerable"
                ) if dep_results else "No dependency manifest found"

                metrics_text = (
                    f"avg_complexity={scoring_metrics.avg_cyclomatic_complexity:.1f}, "
                    f"total_methods={scoring_metrics.total_methods}, "
                    f"long_methods={scoring_metrics.long_methods}, "
                    f"large_files={scoring_metrics.large_files}, "
                    f"test_files={scoring_metrics.test_file_count}"
                )

                ai_result = await generate_recommendations(
                    repo_name=project.name,
                    languages=project.detected_languages or {},
                    total_files=project.total_files,
                    total_loc=project.total_loc,
                    metrics_summary=metrics_text,
                    top_issues=top_issues_text,
                    dependency_summary=dep_text,
                    provider=get_ai_provider(),
                )

                if ai_result.get("executive_summary"):
                    analysis.summary = {"executive_summary": ai_result["executive_summary"]}

                for rec in ai_result.get("recommendations", [])[:10]:
                    db.add(Recommendation(
                        analysis_id=analysis.id,
                        category=rec.get("category", "refactor"),
                        priority=rec.get("priority", "medium"),
                        title=rec.get("title", "")[:500],
                        description=rec.get("description"),
                        rationale=rec.get("rationale"),
                        implementation_steps="\n".join(
                            str(s) for s in rec.get("implementation_steps", [])
                        ) if isinstance(rec.get("implementation_steps"), list)
                        else rec.get("implementation_steps"),
                        estimated_hours=rec.get("estimated_hours"),
                        impact_score=rec.get("impact_score"),
                        affected_files=rec.get("affected_files") or [],
                    ))
            except Exception as ai_err:
                logger.warning("AI analysis failed (non-fatal): %s", ai_err)

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
                except Exception as exc:
                    logger.warning("Failed to clean up temp dir %s: %s", tmp_dir, exc)
