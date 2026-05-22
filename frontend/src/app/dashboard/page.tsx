"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import {
  FolderGit2,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Plus,
  TrendingUp,
  Shield,
  Package,
  Loader2,
} from "lucide-react";
import { listProjects, setAuthToken } from "@/lib/api-client";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = (session as any)?.backendToken as string | undefined;
    setAuthToken(token ?? null);
    listProjects(0, 100)
      .then((res) => setProjects(res.projects))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [status, session]);

  const completedProjects = projects.filter((p) => p.status === "completed");
  const avgScore =
    completedProjects.length > 0
      ? Math.round(
          completedProjects.reduce((sum, p) => sum + (p.overall_score ?? 0), 0) /
            completedProjects.length,
        )
      : null;
  const totalDebt = projects.reduce((sum, p) => sum + (p.debt_count ?? 0), 0);
  const totalVulnDeps = projects.reduce((sum, p) => sum + (p.vulnerable_dep_count ?? 0), 0);

  const STATS = [
    {
      label: "Total Projects",
      value: loading ? "…" : String(projects.length),
      icon: FolderGit2,
      color: "text-primary",
      bg: "bg-primary/10",
    },
    {
      label: "Avg. Score",
      value: loading ? "…" : avgScore !== null ? String(avgScore) : "—",
      icon: TrendingUp,
      color: "text-green-500",
      bg: "bg-green-500/10",
    },
    {
      label: "Open Debt Items",
      value: loading ? "…" : String(totalDebt),
      icon: AlertTriangle,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
    },
    {
      label: "Vulnerable Deps",
      value: loading ? "…" : String(totalVulnDeps),
      icon: Shield,
      color: "text-destructive",
      bg: "bg-destructive/10",
    },
  ];

  return (
    <div className="space-y-8 animate-[fade-in_0.5s_ease-out]">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Welcome back 👋</h1>
          <p className="mt-1 text-muted-foreground">
            Here&apos;s an overview of your modernization progress.
          </p>
        </div>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center gap-2 rounded-xl gradient-primary px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl"
        >
          <Plus className="h-4 w-4" />
          New Project
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((stat, i) => (
          <div
            key={stat.label}
            className="glass rounded-xl p-5 card-hover"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className={`rounded-lg ${stat.bg} p-2.5 w-fit`}>
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </div>
            <div className="mt-4">
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="mt-1 text-xs text-muted-foreground">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Projects list or empty state */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : projects.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center glow-border">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <FolderGit2 className="h-8 w-8 text-primary" />
          </div>
          <h3 className="mb-2 text-xl font-semibold">No projects yet</h3>
          <p className="mb-6 text-muted-foreground">
            Connect a GitHub repository to get started with your first modernization analysis.
          </p>
          <Link
            href="/dashboard/projects/new"
            className="inline-flex items-center gap-2 rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl"
          >
            <Plus className="h-4 w-4" />
            Analyze Your First Repository
          </Link>
        </div>
      ) : (
        <div className="glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Recent Projects</h3>
            <Link
              href="/dashboard/projects"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <Link
                key={project.id}
                href={`/dashboard/projects/${project.id}`}
                className="flex items-center justify-between rounded-lg bg-muted/50 p-3 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FolderGit2 className="h-4 w-4 text-primary shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{project.name}</p>
                    {project.repo_full_name && (
                      <p className="text-xs text-muted-foreground truncate">
                        {project.repo_full_name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {project.total_files > 0 && (
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      {project.total_files} files
                    </span>
                  )}
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      project.status === "completed"
                        ? "bg-green-500/10 text-green-500"
                        : project.status === "analyzing"
                          ? "bg-primary/10 text-primary"
                          : project.status === "failed"
                            ? "bg-destructive/10 text-destructive"
                            : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {project.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          {
            icon: Package,
            title: "Dependency Audit",
            desc: "Check all packages for vulnerabilities and updates.",
            color: "text-accent",
            href: "/dashboard/projects",
          },
          {
            icon: BarChart3,
            title: "Score Trends",
            desc: "Track modernization progress over time.",
            color: "text-green-500",
            href: "/dashboard/projects",
          },
          {
            icon: CheckCircle2,
            title: "AI Recommendations",
            desc: "Review and act on AI-generated insights.",
            color: "text-primary",
            href: "/dashboard/projects",
          },
        ].map((action) => (
          <Link
            key={action.title}
            href={action.href}
            className="group glass rounded-xl p-6 card-hover"
          >
            <action.icon className={`h-6 w-6 ${action.color} mb-3`} />
            <h4 className="font-semibold">{action.title}</h4>
            <p className="mt-1 text-sm text-muted-foreground">{action.desc}</p>
            <div className="mt-4 flex items-center text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
              Get Started <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
