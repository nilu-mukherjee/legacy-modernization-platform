import { BarChart3, TrendingUp, GitCompare, Clock, Sparkles } from "lucide-react";

const PLANNED = [
  {
    icon: TrendingUp,
    title: "Score Trends",
    desc: "Track modernization scores over time across all your repositories.",
  },
  {
    icon: GitCompare,
    title: "Before / After Comparisons",
    desc: "Visualise how debt, complexity, and dependencies changed between analyses.",
  },
  {
    icon: Clock,
    title: "Analysis History",
    desc: "Full timeline of every analysis run with diffs and progression charts.",
  },
];

export default function AnalyticsPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center space-y-10 animate-[fade-in_0.5s_ease-out]">
      <div className="text-center space-y-4">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 ring-1 ring-primary/20 mb-6">
          <BarChart3 className="h-10 w-10 text-primary" />
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-4 py-1.5 text-xs font-medium text-primary">
          <Sparkles className="h-3 w-3" />
          Coming Soon
        </div>
        <h1 className="text-4xl font-bold tracking-tight">Analytics</h1>
        <p className="max-w-md text-muted-foreground text-sm leading-relaxed">
          Deep-dive charts and trend data for your modernization journey.
          Understand where you&apos;ve been and where you&apos;re headed.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3 w-full max-w-2xl">
        {PLANNED.map((f) => (
          <div key={f.title} className="glass rounded-xl p-5 space-y-2 opacity-75">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <f.icon className="h-4 w-4 text-primary" />
            </div>
            <p className="text-sm font-semibold">{f.title}</p>
            <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
