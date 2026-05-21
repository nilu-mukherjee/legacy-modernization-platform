/**
 * Project Detail Page
 * ===================
 * Shows full analysis results for a single project:
 * score gauge, radar chart, debt items, dependencies, and recommendations.
 *
 * This is a client component that fetches data from the API.
 */

"use client";

import { useEffect, useState } from "react";
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
} from "lucide-react";
import ScoreGauge from "@/components/analysis/score-gauge";
import SubScoreRadar from "@/components/analysis/sub-score-radar";
import { severityBgColor } from "@/lib/utils";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    async function loadData() {
      const token = localStorage.getItem("codelens_token");
      const headers = { Authorization: `Bearer ${token}` };

      try {
        const [projRes, analysisRes] = await Promise.all([
          fetch(`/api/v1/projects/${projectId}`, { headers }),
          fetch(`/api/v1/projects/${projectId}/analysis`, { headers }),
        ]);

        if (projRes.ok) setProject(await projRes.json());
        if (analysisRes.ok) setAnalysis(await analysisRes.json());
      } catch {
        // Handle error silently for MVP.
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Demo data for showcase when no real analysis exists yet.
  const score = analysis?.overall_score ?? 45;
  const grade = analysis?.grade ?? "C";
  const subScores = analysis?.sub_scores ?? {
    code_health: 55,
    dependency_health: 30,
    architecture_quality: 45,
    test_coverage: 20,
    documentation: 60,
    infrastructure_readiness: 50,
    security_posture: 70,
  };

  const TABS = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "debt", label: "Tech Debt", icon: AlertTriangle },
    { id: "deps", label: "Dependencies", icon: Package },
    { id: "ai", label: "AI Insights", icon: Bot },
  ];

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
        <button className="inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-medium transition-colors hover:bg-muted">
          <RefreshCw className="h-4 w-4" />
          Re-analyze
        </button>
      </div>

      {/* Score + Radar */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass rounded-xl p-8 flex flex-col items-center justify-center glow-border">
          <h3 className="mb-4 text-sm font-medium text-muted-foreground">
            Modernization Readiness
          </h3>
          <ScoreGauge score={score} grade={grade} size={200} />
          <p className="mt-4 text-center text-sm text-muted-foreground max-w-xs">
            {score >= 60
              ? "Good foundation — focus on the priority areas below."
              : "Significant modernization work needed. Start with quick wins."}
          </p>
        </div>

        <div className="glass rounded-xl p-6">
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">
            Score Breakdown
          </h3>
          <SubScoreRadar subScores={subScores} height={280} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border pb-px">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
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
        {activeTab === "overview" && (
          <div className="space-y-4">
            <h3 className="font-semibold">Project Stats</h3>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                { label: "Total Files", value: project?.total_files ?? "—" },
                { label: "Lines of Code", value: project?.total_loc?.toLocaleString() ?? "—" },
                { label: "Languages", value: project?.detected_languages ? Object.keys(project.detected_languages).length : "—" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-lg bg-muted/50 p-4">
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-xs text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {activeTab === "debt" && (
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="mx-auto h-8 w-8 mb-3 text-warning" />
            <p>Technical debt items will appear here after analysis completes.</p>
          </div>
        )}
        {activeTab === "deps" && (
          <div className="text-center py-8 text-muted-foreground">
            <Package className="mx-auto h-8 w-8 mb-3 text-accent" />
            <p>Dependency health data will appear here after analysis completes.</p>
          </div>
        )}
        {activeTab === "ai" && (
          <div className="text-center py-8 text-muted-foreground">
            <Bot className="mx-auto h-8 w-8 mb-3 text-primary" />
            <p>AI recommendations will appear here after analysis completes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
