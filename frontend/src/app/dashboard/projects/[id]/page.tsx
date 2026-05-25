"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  BarChart3,
  Package,
  AlertTriangle,
  Bot,
  FileCode2,
  RefreshCw,
  Loader2,
  ExternalLink,
  Bug,
  ShieldAlert,
  Lightbulb,
  Palette,
  BookOpen,
} from "lucide-react";
import ScoreGauge from "@/components/analysis/score-gauge";
import SubScoreRadar from "@/components/analysis/sub-score-radar";
import CreatePRButton from "@/components/analysis/create-pr-button";
import { severityBgColor } from "@/lib/utils";
import {
  getProject,
  getAnalysis,
  getDebtItems,
  getDependencies,
  getRecommendations,
  reAnalyze,
  setAuthToken,
} from "@/lib/api-client";
import { useSession } from "next-auth/react";
import { useJobStatus } from "@/hooks/use-job-status";
import { Pagination } from "@/components/ui/pagination";

const LANG_COLORS: Record<string, string> = {
  python: "#3572A5",
  javascript: "#f1e05a",
  typescript: "#2b7489",
  java: "#b07219",
  go: "#00ADD8",
  rust: "#dea584",
  ruby: "#701516",
  csharp: "#178600",
  cpp: "#f34b7d",
  c: "#555555",
  php: "#4F5D95",
  swift: "#F05138",
  kotlin: "#A97BFF",
  scala: "#c22d40",
  dart: "#00B4AB",
  vbnet: "#945db7",
  vb6: "#945db7",
  objectivec: "#438eff",
  cobol: "#005CA5",
  abap: "#E8274B",
  apex: "#1797C0",
  jcl: "#6e4a7e",
  rpg: "#0033A0",
  plsql: "#dad8d8",
  pli: "#6e4a7e",
  sql: "#e38c00",
  terraform: "#7B42BC",
  bicep: "#0078D4",
  helm: "#0F1689",
  shell: "#89e051",
  html: "#e34c26",
  css: "#563d7c",
  scss: "#c6538c",
  "jupyter notebook": "#DA5B0B",
  makefile: "#427819",
  dockerfile: "#384d54",
  mako: "#9a1a1a",
  yaml: "#cb171e",
  json: "#292929",
  xml: "#0060ac",
};

function getLangColor(lang: string): string {
  return LANG_COLORS[lang.toLowerCase()] ?? "#8b8b8b";
}

function LanguageBreakdown({ languages }: { languages: Record<string, number> }) {
  const entries = Object.entries(languages).sort(([, a], [, b]) => b - a);
  const total = entries.reduce((sum, [, n]) => sum + n, 0);
  if (total === 0) return null;

  const withPct = entries.map(([lang, count]) => ({
    lang,
    pct: Math.round((count / total) * 1000) / 10,
  }));

  return (
    <div className="mt-4">
      <h4 className="mb-3 text-sm font-medium">Languages</h4>
      {/* Segmented bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-full mb-3">
        {withPct.map(({ lang, pct }) => (
          <div
            key={lang}
            style={{ width: `${pct}%`, backgroundColor: getLangColor(lang) }}
            title={`${lang} ${pct}%`}
          />
        ))}
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {withPct.map(({ lang, pct }) => (
          <div key={lang} className="flex items-center gap-1.5 text-xs">
            <span
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ backgroundColor: getLangColor(lang) }}
            />
            <span className="font-medium capitalize">{lang}</span>
            <span className="text-muted-foreground">{pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: session, status } = useSession();
  const [project, setProject] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [debt, setDebt] = useState<any>(null);
  const [deps, setDeps] = useState<any>(null);
  const [recs, setRecs] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [debtCategory, setDebtCategory] = useState("all");
  const [debtPage, setDebtPage] = useState(1);
  const [depsPage, setDepsPage] = useState(1);
  const [recsPage, setRecsPage] = useState(1);
  const [debtByCategory, setDebtByCategory] = useState<Record<string, number>>({});
  const DEBT_PAGE_SIZE = 20;
  const DEPS_PAGE_SIZE = 20;
  const RECS_PAGE_SIZE = 10;
  const [reanalyzing, setReanalyzing] = useState(false);
  const [reanalyzeError, setReanalyzeError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [aiLoaded, setAiLoaded] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  async function loadData() {
    try {
      const [projData, analysisData] = await Promise.all([
        getProject(projectId),
        getAnalysis(projectId).catch(() => null),
      ]);
      setProject(projData);
      setAnalysis(analysisData);

      if (analysisData) {
        const [debtData, depsData] = await Promise.all([
          getDebtItems(projectId, 0, DEBT_PAGE_SIZE).catch(() => null),
          getDependencies(projectId, 0, DEPS_PAGE_SIZE).catch(() => null),
        ]);
        setDebt(debtData);
        setDeps(depsData);
        if (debtData?.by_category) setDebtByCategory(debtData.by_category);
      }
    } catch {
      // project not found or unauthorized
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = (session as any)?.backendToken as string | undefined;
    setAuthToken(token ?? null);
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, session, projectId]);

  // If project is completed but analysis missing (race on initial load), retry once
  useEffect(() => {
    if (!project || analysis) return;
    if (project.status !== "completed") return;
    let cancelled = false;
    (async () => {
      for (let i = 0; i < 5; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        if (cancelled) return;
        const a = await getAnalysis(projectId).catch(() => null);
        if (a) {
          setAnalysis(a);
          const [debtData, depsData] = await Promise.all([
            getDebtItems(projectId, 0, DEBT_PAGE_SIZE).catch(() => null),
            getDependencies(projectId, 0, DEPS_PAGE_SIZE).catch(() => null),
          ]);
          if (!cancelled) {
            setDebt(debtData);
            setDeps(depsData);
            if (debtData?.by_category) setDebtByCategory(debtData.by_category);
          }
          return;
        }
      }
    })();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.status, project?.id, analysis]);

  // Poll while analysis is running
  useEffect(() => {
    if (!project) return;
    if (project.status !== "analyzing") return;
    const interval = setInterval(async () => {
      try {
        const [projData, analysisData] = await Promise.all([
          getProject(projectId),
          getAnalysis(projectId).catch(() => null),
        ]);
        setProject(projData);
        setAnalysis(analysisData);
        if (projData.status !== "analyzing") {
          clearInterval(interval);
          // Retry up to 5s for analysis row to become visible after DB commit
          let finalAnalysis = analysisData;
          if (!finalAnalysis) {
            for (let i = 0; i < 5; i++) {
              await new Promise((r) => setTimeout(r, 1000));
              finalAnalysis = await getAnalysis(projectId).catch(() => null);
              if (finalAnalysis) break;
            }
          }
          setAnalysis(finalAnalysis);
          if (finalAnalysis) {
            const [debtData, depsData] = await Promise.all([
              getDebtItems(projectId, 0, DEBT_PAGE_SIZE).catch(() => null),
              getDependencies(projectId, 0, DEPS_PAGE_SIZE).catch(() => null),
            ]);
            setDebt(debtData);
            setDeps(depsData);
            if (debtData?.by_category) setDebtByCategory(debtData.by_category);
          }
        }
      } catch {
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [project?.status, projectId]);

  async function handleReanalyze() {
    setReanalyzeError(null);
    setReanalyzing(true);
    setAnalysis(null);
    setDebt(null);
    setDeps(null);
    setRecs(null);
    setAiLoaded(false);
    try {
      const res = await reAnalyze(projectId);
      setActiveJobId(res.job_id);
      setProject((p: any) => ({ ...p, status: "analyzing" }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Re-analyze failed";
      setReanalyzeError(msg);
      // Restore project status so the button re-enables.
      setProject((p: any) => ({ ...p, status: p?.status === "analyzing" ? "failed" : p?.status }));
    } finally {
      setReanalyzing(false);
    }
  }

  const { progress, currentStep, isComplete: jobDone } = useJobStatus(activeJobId);

  // Reload data when job finishes
  useEffect(() => {
    if (!jobDone || !activeJobId) return;
    setActiveJobId(null);
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobDone]);

  // Refetch debt when page or category changes (skip on initial defaults — loadData covers it).
  useEffect(() => {
    if (!analysis || (debtPage === 1 && debtCategory === "all")) return;
    const cat = debtCategory === "all" ? undefined : debtCategory;
    getDebtItems(projectId, (debtPage - 1) * DEBT_PAGE_SIZE, DEBT_PAGE_SIZE, cat)
      .then((d) => { setDebt(d); if (d.by_category) setDebtByCategory(d.by_category); })
      .catch(() => null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debtPage, debtCategory]);

  // Refetch deps when page changes.
  useEffect(() => {
    if (!analysis || depsPage === 1) return;
    getDependencies(projectId, (depsPage - 1) * DEPS_PAGE_SIZE, DEPS_PAGE_SIZE)
      .then((d) => setDeps(d))
      .catch(() => null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [depsPage]);

  // Refetch recs when page changes.
  useEffect(() => {
    if (!analysis || recsPage === 1) return;
    getRecommendations(projectId, (recsPage - 1) * RECS_PAGE_SIZE, RECS_PAGE_SIZE)
      .then((r) => setRecs(r))
      .catch(() => null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recsPage]);

  // Lazy-load AI recommendations when AI tab is first opened
  useEffect(() => {
    const analyzing = reanalyzing || project?.status === "analyzing";
    if (activeTab !== "ai" || aiLoaded || !analysis || analyzing) return;
    setAiLoading(true);
    getRecommendations(projectId, 0, RECS_PAGE_SIZE)
      .then((r) => { setRecs(r); setAiLoaded(true); })
      .catch(() => setAiLoaded(true))
      .finally(() => setAiLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, analysis, aiLoaded, reanalyzing, project?.status]);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // True as soon as Re-analyze is clicked (reanalyzing) AND while the worker runs.
  const isAnalyzing = reanalyzing || project?.status === "analyzing";
  const score = analysis?.overall_score ?? null;
  const grade = analysis?.grade ?? "?";
  const subScores = analysis?.sub_scores ?? {
    code_health: 0,
    dependency_health: 0,
    architecture_quality: 0,
    test_coverage: 0,
    documentation: 0,
    infrastructure_readiness: 0,
    security_posture: 0,
  };

  const TABS = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "debt", label: "Tech Debt", icon: AlertTriangle },
    { id: "deps", label: "Dependencies", icon: Package },
    { id: "ai", label: "AI Insights", icon: Bot },
  ];

  const DEBT_CATEGORIES = [
    { id: "all", label: "All", icon: AlertTriangle, desc: "", color: "text-muted-foreground" },
    { id: "bug_risk", label: "Bug Risk", icon: Bug, desc: "Error-prone, slow, or incompatible code", color: "text-orange-500" },
    { id: "security", label: "Security", icon: ShieldAlert, desc: "Insecure code, hardcoded credentials and vulnerable dependencies", color: "text-red-500" },
    { id: "best_practices", label: "Best Practices", icon: Lightbulb, desc: "Complex, unused, or unreachable code", color: "text-blue-400" },
    { id: "code_style", label: "Code Style", icon: Palette, desc: "Code with formatting or syntax issues", color: "text-purple-400" },
    { id: "documentation", label: "Documentation", icon: BookOpen, desc: "Issues with method and class comment annotations", color: "text-teal-400" },
  ];

  const debtItems: any[] = debt?.debt_items ?? [];
  const debtTotal: number = debt?.total ?? 0;
  const depsItems: any[] = deps?.dependencies ?? [];
  const depsTotal: number = deps?.total ?? 0;
  const recsItems: any[] = recs?.recommendations ?? [];
  const recsTotal: number = recs?.total ?? 0;

  function debtCategoryCount(id: string) {
    if (id === "all") return Object.values(debtByCategory).reduce((a, b) => a + b, 0);
    return debtByCategory[id] ?? 0;
  }

  return (
    <div className="space-y-6 animate-[fade-in_0.5s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/dashboard/projects"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Projects
          </Link>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <FileCode2 className="h-6 w-6 text-primary" />
            {project?.name || "Project"}
          </h1>
          {project?.repo_url && (
            <a
              href={project.repo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              {project.repo_full_name}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        <button
          onClick={handleReanalyze}
          disabled={reanalyzing || isAnalyzing}
          className="inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-medium transition-colors hover:bg-muted disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${reanalyzing || isAnalyzing ? "animate-spin" : ""}`} />
          {reanalyzing ? "Starting…" : project?.status === "analyzing" ? "Analyzing…" : "Re-analyze"}
        </button>
      </div>

      {/* Error banner */}
      {reanalyzeError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {reanalyzeError}
        </div>
      )}

      {/* Progress banner while analyzing */}
      {isAnalyzing && (
        <div className="glass rounded-xl p-4 border border-primary/20 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
              <span className="text-sm font-medium">{currentStep || "Initializing…"}</span>
            </div>
            <span className="text-sm font-bold text-primary">{progress}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Score + Radar */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass rounded-xl p-8 flex flex-col items-center justify-center glow-border">
          <h3 className="mb-4 text-sm font-medium text-muted-foreground">
            Modernization Readiness
          </h3>
          {isAnalyzing ? (
            <div className="flex flex-col items-center gap-4 w-full">
              <div className="h-[200px] w-[200px] rounded-full bg-muted animate-pulse" />
              <div className="h-4 w-24 rounded bg-muted animate-pulse" />
            </div>
          ) : score !== null ? (
            <ScoreGauge score={score} grade={grade} size={200} />
          ) : (
            <div className="flex h-[200px] items-center justify-center text-muted-foreground text-sm">
              No score yet
            </div>
          )}
        </div>

        <div className="glass rounded-xl p-6">
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">
            Score Breakdown
          </h3>
          {isAnalyzing ? (
            <div className="space-y-3 pt-4">
              {Array.from({ length: 7 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="h-3 w-16 rounded bg-muted animate-pulse" />
                  <div className="h-2 flex-1 rounded-full bg-muted animate-pulse" style={{ animationDelay: `${i * 80}ms` }} />
                </div>
              ))}
            </div>
          ) : (
            <SubScoreRadar subScores={subScores} height={280} />
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border pb-px">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{ cursor: "pointer" }}
            className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="glass rounded-xl p-6">
        {isAnalyzing && (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 rounded-lg bg-muted animate-pulse" style={{ animationDelay: `${i * 60}ms`, opacity: 1 - i * 0.15 }} />
            ))}
          </div>
        )}
        {!isAnalyzing && activeTab === "overview" && (

          <div className="space-y-4">
            <h3 className="font-semibold">Project Stats</h3>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                {
                  label: "Total Files",
                  value:
                    project?.total_files > 0
                      ? project.total_files
                      : isAnalyzing
                        ? "…"
                        : "—",
                },
                {
                  label: "Lines of Code",
                  value:
                    project?.total_loc > 0
                      ? project.total_loc.toLocaleString()
                      : isAnalyzing
                        ? "…"
                        : "—",
                },
                {
                  label: "Languages",
                  value:
                    project?.detected_languages &&
                    Object.keys(project.detected_languages).length > 0
                      ? Object.keys(project.detected_languages).length
                      : isAnalyzing
                        ? "…"
                        : "—",
                },
              ].map((stat) => (
                <div key={stat.label} className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-xs text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>

            {project?.detected_languages &&
              Object.keys(project.detected_languages).length > 0 && (
                <LanguageBreakdown languages={project.detected_languages} />
              )}
          </div>
        )}

        {!isAnalyzing && activeTab === "debt" && (
          <div className="space-y-4">
            {/* Category filter chips */}
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
              {DEBT_CATEGORIES.map((cat) => {
                const count = debtCategoryCount(cat.id);
                const active = debtCategory === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => { setDebtCategory(cat.id); setDebtPage(1); }}
                    style={{ cursor: "pointer" }}
                    className={`flex flex-col items-center gap-1 rounded-xl border px-2 py-3 text-center transition-all ${
                      active
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/40 hover:bg-muted/50"
                    }`}
                    title={cat.desc || undefined}
                  >
                    <cat.icon className={`h-4 w-4 ${active ? "text-primary" : cat.color}`} />
                    <span className={`text-xs font-medium leading-tight ${active ? "text-primary" : "text-foreground"}`}>
                      {cat.label}
                    </span>
                    <span className={`text-xs font-bold ${active ? "text-primary" : "text-muted-foreground"}`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Active category description */}
            {debtCategory !== "all" && (
              <p className="text-xs text-muted-foreground">
                {DEBT_CATEGORIES.find((c) => c.id === debtCategory)?.desc}
              </p>
            )}

            {/* Debt items */}
            {debtTotal > 0 ? (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  {debtTotal} issue{debtTotal !== 1 ? "s" : ""}
                  {debtCategory !== "all" ? ` in ${DEBT_CATEGORIES.find((c) => c.id === debtCategory)?.label}` : " total"}
                </p>
                {debtItems.map((item: any, i: number) => (
                  <div key={i} className="rounded-lg border border-border p-3 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold shrink-0 ${severityBgColor(item.severity)}`}>
                        {item.severity}
                      </span>
                      {debtCategory === "all" && (
                        <span className={`inline-flex items-center gap-1 text-xs font-medium shrink-0 ${
                          DEBT_CATEGORIES.find((c) => c.id === item.category)?.color ?? "text-muted-foreground"
                        }`}>
                          {(() => { const cat = DEBT_CATEGORIES.find((c) => c.id === item.category); return cat ? <cat.icon className="h-3 w-3" /> : null; })()}
                          {DEBT_CATEGORIES.find((c) => c.id === item.category)?.label ?? item.category}
                        </span>
                      )}
                      <span className="text-sm font-medium">{item.title}</span>
                    </div>
                    {item.file_path && (
                      <p className="text-xs text-muted-foreground font-mono truncate">
                        {item.file_path}{item.line_start ? `:${item.line_start}` : ""}
                      </p>
                    )}
                    {item.suggestion && (
                      <p className="text-xs text-muted-foreground">{item.suggestion}</p>
                    )}
                  </div>
                ))}
                <Pagination
                  page={debtPage}
                  pageSize={DEBT_PAGE_SIZE}
                  total={debtTotal}
                  onChange={setDebtPage}
                />
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="mx-auto h-8 w-8 mb-3 text-yellow-500/50" />
                <p className="text-sm">
                  {Object.keys(debtByCategory).length === 0 ? "No tech debt items found." : "No issues in this category."}
                </p>
              </div>
            )}
          </div>
        )}

        {!isAnalyzing && activeTab === "deps" && (
          <div>
            {depsTotal > 0 ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  {depsTotal} dependencies analyzed
                </p>
                {depsItems.map((dep: any, i: number) => (
                  <div
                    key={i}
                    className="rounded-lg border border-border p-3 flex items-center justify-between"
                  >
                    <div>
                      <span className="text-sm font-medium">
                        {dep.package_name}
                      </span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {dep.current_version}
                      </span>
                      {dep.latest_version &&
                        dep.latest_version !== dep.current_version && (
                          <span className="ml-1 text-xs text-yellow-500">
                            → {dep.latest_version}
                          </span>
                        )}
                    </div>
                    <span
                      className={`text-xs font-medium ${
                        dep.risk_level === "critical"
                          ? "text-red-500"
                          : dep.risk_level === "high"
                            ? "text-orange-500"
                            : "text-muted-foreground"
                      }`}
                    >
                      {dep.risk_level}
                    </span>
                  </div>
                ))}
                <Pagination
                  page={depsPage}
                  pageSize={DEPS_PAGE_SIZE}
                  total={depsTotal}
                  onChange={setDepsPage}
                />
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Package className="mx-auto h-8 w-8 mb-3 text-accent" />
                <p>
                  {isAnalyzing
                    ? "Analysis in progress…"
                    : "No dependency data found."}
                </p>
              </div>
            )}
          </div>
        )}

        {!isAnalyzing && activeTab === "ai" && (
          <div>
            {aiLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" style={{ animationDelay: `${i * 80}ms` }} />
                ))}
              </div>
            ) : recsTotal > 0 ? (
              <div className="space-y-4">
                <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 px-3 py-2 flex items-start gap-2">
                  <Bot className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-xs text-muted-foreground">
                    AI-generated insights may contain errors. Always review suggested changes before applying them to production code.
                  </p>
                </div>
                {analysis?.summary?.executive_summary && (
                  <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
                    <p className="text-sm font-medium text-primary mb-1">Executive Summary</p>
                    <p className="text-sm text-muted-foreground">{analysis.summary.executive_summary}</p>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">{recsTotal} recommendations</p>
                  <button
                    onClick={() => { setAiLoaded(false); }}
                    style={{ cursor: "pointer" }}
                    title="Refresh recommendations"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </div>
                {recsItems.map((rec: any, i: number) => (
                  <div key={i} className="rounded-lg border border-border p-4 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-semibold">{rec.title}</span>
                      <div className="flex gap-1 shrink-0">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                          rec.priority === "critical" ? "bg-red-500/10 text-red-500" :
                          rec.priority === "high" ? "bg-orange-500/10 text-orange-500" :
                          rec.priority === "medium" ? "bg-yellow-500/10 text-yellow-500" :
                          "bg-muted text-muted-foreground"
                        }`}>{rec.priority}</span>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium">{rec.category}</span>
                      </div>
                    </div>
                    {rec.description && (
                      <p className="text-xs text-muted-foreground">{rec.description}</p>
                    )}
                    <div className="flex items-center justify-between gap-4 flex-wrap">
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        {rec.estimated_hours && <span>~{rec.estimated_hours}h effort</span>}
                        {rec.impact_score && <span>Impact: {rec.impact_score}/10</span>}
                      </div>
                      {project?.repo_url && (session as any)?.accessToken && (
                        <CreatePRButton
                          rec={rec}
                          repoUrl={project.repo_url}
                          accessToken={(session as any).accessToken}
                          projectId={projectId}
                          backendToken={(session as any)?.backendToken ?? ""}
                        />
                      )}
                    </div>
                  </div>
                ))}
                <Pagination
                  page={recsPage}
                  pageSize={RECS_PAGE_SIZE}
                  total={recsTotal}
                  onChange={setRecsPage}
                />
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Bot className="mx-auto h-10 w-10 mb-4 text-primary/50" />
                <p className="text-sm mb-4">No AI insights yet for this project.</p>
                <button
                  onClick={handleReanalyze}
                  disabled={reanalyzing}
                  style={{ cursor: "pointer" }}
                  className="inline-flex items-center gap-2 rounded-xl gradient-primary px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl disabled:opacity-50"
                >
                  {reanalyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
                  {reanalyzing ? "Starting…" : "Generate AI Insights"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
