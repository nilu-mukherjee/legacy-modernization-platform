"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  getProject,
  getAnalysis,
  getDebtItems,
  getDependencies,
  getRecommendations,
  setAuthToken,
} from "@/lib/api-client";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];
const SEVERITY_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#d97706",
  low: "#6b7280",
};

const DIMENSION_LABELS: Record<string, string> = {
  code_health: "Code Health",
  dependency_health: "Dependency Health",
  architecture_quality: "Architecture Quality",
  test_coverage: "Test Coverage",
  documentation: "Documentation",
  infrastructure_readiness: "Infrastructure Readiness",
  security_posture: "Security Posture",
};

function scoreColor(score: number) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#eab308";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

function ScoreGauge({ score, grade }: { score: number; grade: string }) {
  const r = 46;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const color = scoreColor(score);

  return (
    <div style={{ textAlign: "center", minWidth: 120 }}>
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
        <text x="60" y="55" textAnchor="middle" fontSize="22" fontWeight="800" fill={color}>
          {Math.round(score)}%
        </text>
        <text x="60" y="74" textAnchor="middle" fontSize="13" fontWeight="700" fill="#6b7280">
          Grade {grade}
        </text>
      </svg>
      <div style={{ fontSize: "0.65rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: "-4px" }}>
        Modernization Score
      </div>
    </div>
  );
}

export default function ReportPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: session, status } = useSession();

  const [project, setProject] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [debt, setDebt] = useState<any>(null);
  const [deps, setDeps] = useState<any>(null);
  const [recs, setRecs] = useState<any>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = (session as any)?.backendToken as string | undefined;
    setAuthToken(token ?? null);

    Promise.all([
      getProject(projectId),
      getAnalysis(projectId).catch(() => null),
      getDebtItems(projectId, 0, 200).catch(() => null),
      getDependencies(projectId, 0, 100).catch(() => null),
      getRecommendations(projectId, 0, 20).catch(() => null),
    ])
      .then(([proj, anal, d, dp, rc]) => {
        setProject(proj);
        setAnalysis(anal);
        setDebt(d);
        setDeps(dp);
        setRecs(rc);
        setReady(true);
      })
      .catch(() => setError("Failed to load report data."));
  }, [status, session, projectId]);

  if (error) {
    return (
      <div style={{ padding: "2rem", fontFamily: "sans-serif", color: "#ef4444" }}>
        {error}
      </div>
    );
  }

  if (!ready || !project) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", fontFamily: "sans-serif", color: "#888" }}>
        Preparing report…
      </div>
    );
  }

  const score: number | null = analysis?.overall_score ?? null;
  const grade: string = analysis?.grade ?? "—";
  const subScores: Record<string, number> = analysis?.sub_scores ?? {};
  const execSummary: string = analysis?.summary?.executive_summary ?? "";
  const debtItems: any[] = debt?.debt_items ?? [];
  const byCategory: Record<string, number> = debt?.by_category ?? {};
  const dependencies: any[] = deps?.dependencies ?? [];
  const recommendations: any[] = recs?.recommendations ?? [];

  const vulnDeps = dependencies.filter((d) => d.vulnerability_count > 0);
  const outdatedDeps = dependencies.filter((d) => d.days_behind > 365);

  const debtBySeverity: Record<string, number> = {};
  for (const item of debtItems) {
    const s = item.severity ?? "low";
    debtBySeverity[s] = (debtBySeverity[s] ?? 0) + 1;
  }

  const generatedAt = new Date().toLocaleDateString("en-US", {
    year: "numeric", month: "long", day: "numeric",
  });

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: "Inter", "Segoe UI", system-ui, sans-serif; color: #111; background: #fff; font-size: 14px; }
        .page { max-width: 920px; margin: 0 auto; padding: 3rem 2.5rem; }
        .print-btn {
          position: fixed; top: 1.5rem; right: 1.5rem; z-index: 100;
          background: #4f46e5; color: #fff; border: none; border-radius: 0.5rem;
          padding: 0.6rem 1.25rem; font-size: 0.85rem; font-weight: 600;
          cursor: pointer; display: flex; align-items: center; gap: 0.4rem;
          box-shadow: 0 2px 8px rgba(79,70,229,0.3);
        }
        .print-btn:hover { background: #4338ca; }

        /* Header */
        .header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 3px solid #4f46e5; gap: 2rem; }
        .logo { display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; font-weight: 700; color: #4f46e5; margin-bottom: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .project-name { font-size: 1.75rem; font-weight: 800; color: #111; line-height: 1.2; }
        .meta { font-size: 0.78rem; color: #6b7280; margin-top: 0.3rem; }

        /* Stats row */
        .stats-row { display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
        .stat-box { flex: 1; min-width: 110px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 0.75rem 1rem; }
        .stat-value { font-size: 1.5rem; font-weight: 800; color: #111; line-height: 1; }
        .stat-label { font-size: 0.65rem; font-variant: small-caps; letter-spacing: 0.05em; color: #9ca3af; margin-top: 0.2rem; }

        /* Severity legend */
        .sev-legend { display: flex; gap: 1rem; margin-top: 0.75rem; flex-wrap: wrap; }
        .sev-dot { display: flex; align-items: center; gap: 0.3rem; font-size: 0.72rem; color: #374151; font-variant: small-caps; }
        .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

        /* Sections */
        section { margin-bottom: 2.5rem; }
        .section-title { font-size: 0.7rem; font-variant: small-caps; letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.75rem; padding-bottom: 0.4rem; border-bottom: 1px solid #e5e7eb; }

        /* Score breakdown */
        .score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
        .score-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; background: #f9fafb; border-radius: 0.375rem; }
        .score-name { font-size: 0.78rem; color: #374151; min-width: 155px; }
        .bar-wrap { flex: 1; height: 5px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
        .bar { height: 100%; border-radius: 3px; }
        .score-val { font-size: 0.8rem; font-weight: 700; min-width: 28px; text-align: right; }

        /* Category chips */
        .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
        .chip { padding: 0.2rem 0.6rem; background: #f3f4f6; border-radius: 999px; font-size: 0.7rem; color: #374151; }
        .chip strong { font-weight: 700; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
        th { text-align: left; padding: 0.5rem 0.75rem; background: #f3f4f6; font-weight: 600; color: #374151; font-variant: small-caps; font-size: 0.72rem; letter-spacing: 0.04em; }
        td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #f3f4f6; color: #374151; vertical-align: top; }
        tr:last-child td { border-bottom: none; }
        .th-red { background: #fef2f2; color: #991b1b; }
        .th-amber { background: #fffbeb; color: #92400e; }

        .badge { display: inline-block; padding: 0.12rem 0.45rem; border-radius: 999px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: #fff; letter-spacing: 0.04em; }
        .mono { font-family: "JetBrains Mono", "Fira Code", monospace; font-size: 0.72rem; }

        /* Debt table */
        .debt-title { font-weight: 600; color: #111; margin-bottom: 0.1rem; }
        .debt-suggestion { font-size: 0.72rem; color: #6b7280; }
        .file-path { font-family: monospace; font-size: 0.7rem; color: #6b7280; }

        /* Rec cards */
        .rec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
        .rec-card { padding: 0.75rem; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0.5rem; }
        .rec-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem; }
        .rec-title { font-size: 0.82rem; font-weight: 600; color: #111; }
        .rec-desc { font-size: 0.75rem; color: #6b7280; line-height: 1.5; }
        .rec-meta { font-size: 0.68rem; color: #9ca3af; margin-top: 0.3rem; font-variant: small-caps; }

        /* Summary box */
        .summary-box { background: #f0f9ff; border-left: 3px solid #4f46e5; border-radius: 0.375rem; padding: 0.75rem 1rem; font-size: 0.82rem; color: #374151; line-height: 1.6; margin-bottom: 2rem; }

        /* Footer */
        .footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.7rem; color: #9ca3af; display: flex; justify-content: space-between; }

        @media print {
          .print-btn { display: none; }
          body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
          .page { padding: 1.5rem 2rem; }
          section { page-break-inside: avoid; }
          .rec-grid { grid-template-columns: 1fr 1fr; }
          .score-grid { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      <button className="print-btn" onClick={() => window.print()}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
          <rect x="6" y="14" width="12" height="8"/>
        </svg>
        Download PDF
      </button>

      <div className="page">
        {/* Header */}
        <div className="header">
          <div style={{ flex: 1 }}>
            <div className="logo">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <rect width="20" height="20" rx="5" fill="#4f46e5"/>
                <path d="M5 7h10M5 10h7M5 13h9" stroke="#fff" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              CodeLens AI
            </div>
            <div className="project-name">{project.name}</div>
            <div className="meta">{project.repo_url}</div>
            <div className="meta">Generated {generatedAt}</div>

            {/* Severity legend */}
            <div className="sev-legend" style={{ marginTop: "0.75rem" }}>
              {SEVERITY_ORDER.map((sev) => (
                <span key={sev} className="sev-dot">
                  <span className="dot" style={{ background: SEVERITY_COLOR[sev] }} />
                  {sev} ({debtBySeverity[sev] ?? 0})
                </span>
              ))}
            </div>
          </div>
          {score !== null && <ScoreGauge score={score} grade={grade} />}
        </div>

        {/* Stats row */}
        <div className="stats-row">
          {project.total_files != null && (
            <div className="stat-box">
              <div className="stat-value">{project.total_files.toLocaleString()}</div>
              <div className="stat-label">Files</div>
            </div>
          )}
          {project.total_loc != null && (
            <div className="stat-box">
              <div className="stat-value">{project.total_loc.toLocaleString()}</div>
              <div className="stat-label">Lines of Code</div>
            </div>
          )}
          <div className="stat-box">
            <div className="stat-value">{debt?.total ?? debtItems.length}</div>
            <div className="stat-label">Debt Issues</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{deps?.total ?? dependencies.length}</div>
            <div className="stat-label">Dependencies</div>
          </div>
          {vulnDeps.length > 0 && (
            <div className="stat-box" style={{ borderColor: "#fca5a5" }}>
              <div className="stat-value" style={{ color: "#dc2626" }}>{vulnDeps.length}</div>
              <div className="stat-label">Vulnerable</div>
            </div>
          )}
        </div>

        {/* Executive Summary */}
        {execSummary && (
          <div className="summary-box">{execSummary}</div>
        )}

        {/* Score Breakdown */}
        {Object.keys(subScores).length > 0 && (
          <section>
            <div className="section-title">Score Breakdown</div>
            <div className="score-grid">
              {Object.entries(subScores).map(([key, val]) => {
                const v = Number(val) || 0;
                return (
                  <div key={key} className="score-row">
                    <span className="score-name">{DIMENSION_LABELS[key] ?? key}</span>
                    <div className="bar-wrap">
                      <div className="bar" style={{ width: `${v}%`, background: scoreColor(v) }} />
                    </div>
                    <span className="score-val" style={{ color: scoreColor(v) }}>{Math.round(v)}</span>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Technical Debt */}
        {debtItems.length > 0 && (
          <section>
            <div className="section-title">
              Technical Debt — {debt?.total ?? debtItems.length} issues
            </div>

            {/* Category chips */}
            {Object.keys(byCategory).length > 0 && (
              <div className="chips">
                {Object.entries(byCategory)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cat, cnt]) => (
                    <span key={cat} className="chip">
                      {cat} <strong>{cnt}</strong>
                    </span>
                  ))}
              </div>
            )}

            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Category</th>
                  <th>Issue</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                {SEVERITY_ORDER.flatMap((sev) =>
                  debtItems
                    .filter((item) => item.severity === sev)
                    .slice(0, 10)
                    .map((item: any, i: number) => (
                      <tr key={`${sev}-${i}`}>
                        <td>
                          <span className="badge" style={{ background: SEVERITY_COLOR[sev] }}>
                            {sev}
                          </span>
                        </td>
                        <td style={{ color: "#6b7280", whiteSpace: "nowrap" }}>{item.category}</td>
                        <td>
                          <div className="debt-title">{item.title}</div>
                          {item.suggestion && (
                            <div className="debt-suggestion">{item.suggestion}</div>
                          )}
                        </td>
                        <td>
                          {item.file_path && (
                            <div className="file-path">
                              {item.file_path.split("/").slice(-2).join("/")}
                              {item.line_start ? `:${item.line_start}` : ""}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
            {(debt?.total ?? debtItems.length) > 40 && (
              <p style={{ fontSize: "0.72rem", color: "#9ca3af", marginTop: "0.5rem" }}>
                Showing top issues per severity. {debt?.total ?? debtItems.length} total issues detected.
              </p>
            )}
          </section>
        )}

        {/* Dependency Risk — Vulnerable */}
        {vulnDeps.length > 0 && (
          <section>
            <div className="section-title">Dependency Risk</div>
            <table style={{ marginBottom: outdatedDeps.length > 0 ? "1rem" : 0 }}>
              <thead>
                <tr>
                  <th className="th-red">Package</th>
                  <th className="th-red">Current</th>
                  <th className="th-red">Latest</th>
                  <th className="th-red">CVEs</th>
                  <th className="th-red">Ecosystem</th>
                </tr>
              </thead>
              <tbody>
                {vulnDeps.slice(0, 20).map((dep: any, i: number) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{dep.package_name}</td>
                    <td className="mono">{dep.current_version ?? "—"}</td>
                    <td className="mono">{dep.latest_version ?? "—"}</td>
                    <td>
                      <span className="badge" style={{ background: "#dc2626" }}>
                        {dep.vulnerability_count}
                      </span>
                    </td>
                    <td style={{ color: "#6b7280" }}>{dep.ecosystem ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Severely outdated (>1yr) — separate sub-table */}
            {outdatedDeps.length > 0 && (
              <table>
                <thead>
                  <tr>
                    <th className="th-amber">Package (Outdated &gt;1 year)</th>
                    <th className="th-amber">Current</th>
                    <th className="th-amber">Latest</th>
                    <th className="th-amber">Days Behind</th>
                    <th className="th-amber">Ecosystem</th>
                  </tr>
                </thead>
                <tbody>
                  {outdatedDeps.slice(0, 15).map((dep: any, i: number) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600 }}>{dep.package_name}</td>
                      <td className="mono">{dep.current_version ?? "—"}</td>
                      <td className="mono">{dep.latest_version ?? "—"}</td>
                      <td style={{ color: "#d97706", fontWeight: 600 }}>{dep.days_behind}</td>
                      <td style={{ color: "#6b7280" }}>{dep.ecosystem ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {/* AI Recommendations */}
        {recommendations.length > 0 && (
          <section>
            <div className="section-title">
              AI Recommendations — {recs?.total ?? recommendations.length} total
            </div>
            <div className="rec-grid">
              {recommendations.slice(0, 8).map((rec: any, i: number) => (
                <div key={i} className="rec-card">
                  <div className="rec-header">
                    <span className="badge" style={{ background: SEVERITY_COLOR[rec.priority] ?? "#6b7280" }}>
                      {rec.priority}
                    </span>
                    <span className="rec-title">{rec.title}</span>
                  </div>
                  <div className="rec-desc">{rec.description}</div>
                  {(rec.category || rec.estimated_hours) && (
                    <div className="rec-meta">
                      {rec.category && <span>{rec.category}</span>}
                      {rec.category && rec.estimated_hours && " · "}
                      {rec.estimated_hours && <span>~{rec.estimated_hours}h</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="footer">
          <span>CodeLens AI — AI-Powered Legacy Modernization Platform</span>
          <span>Generated {generatedAt}</span>
        </div>
      </div>
    </>
  );
}
