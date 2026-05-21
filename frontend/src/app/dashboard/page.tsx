/**
 * Dashboard Overview Page
 * =======================
 * Main dashboard page showing aggregate stats, recent projects,
 * and quick actions.
 */

import Link from "next/link";
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
} from "lucide-react";

/** Stat card data for the overview grid. */
const STATS = [
  {
    label: "Total Projects",
    value: "—",
    icon: FolderGit2,
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    label: "Avg. Score",
    value: "—",
    icon: TrendingUp,
    color: "text-success",
    bg: "bg-success/10",
  },
  {
    label: "Open Debt Items",
    value: "—",
    icon: AlertTriangle,
    color: "text-warning",
    bg: "bg-warning/10",
  },
  {
    label: "Vulnerable Deps",
    value: "—",
    icon: Shield,
    color: "text-destructive",
    bg: "bg-destructive/10",
  },
];

export const metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-[fade-in_0.5s_ease-out]">
      {/* ── Welcome Header ─────────────────────────────────────────── */}
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

      {/* ── Stats Grid ─────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((stat, i) => (
          <div
            key={stat.label}
            className="glass rounded-xl p-5 card-hover"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex items-center justify-between">
              <div className={`rounded-lg ${stat.bg} p-2.5`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
            </div>
            <div className="mt-4">
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {stat.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Empty State ────────────────────────────────────────────── */}
      <div className="glass rounded-xl p-12 text-center glow-border">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <FolderGit2 className="h-8 w-8 text-primary" />
        </div>
        <h3 className="mb-2 text-xl font-semibold">No projects yet</h3>
        <p className="mb-6 text-muted-foreground">
          Connect a GitHub repository to get started with your first
          modernization analysis.
        </p>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center gap-2 rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl"
        >
          <Plus className="h-4 w-4" />
          Analyze Your First Repository
        </Link>
      </div>

      {/* ── Quick Actions ──────────────────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          {
            icon: Package,
            title: "Dependency Audit",
            desc: "Check all packages for vulnerabilities and updates.",
            color: "text-accent",
          },
          {
            icon: BarChart3,
            title: "Score Trends",
            desc: "Track modernization progress over time.",
            color: "text-success",
          },
          {
            icon: CheckCircle2,
            title: "AI Recommendations",
            desc: "Review and act on AI-generated insights.",
            color: "text-primary",
          },
        ].map((action) => (
          <div
            key={action.title}
            className="group glass rounded-xl p-6 card-hover cursor-pointer"
          >
            <action.icon className={`h-6 w-6 ${action.color} mb-3`} />
            <h4 className="font-semibold">{action.title}</h4>
            <p className="mt-1 text-sm text-muted-foreground">{action.desc}</p>
            <div className="mt-4 flex items-center text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
              Get Started <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
