import { Bot, Lightbulb, Zap, Shield, Sparkles } from "lucide-react";

const PLANNED = [
  {
    icon: Lightbulb,
    title: "Prioritised Roadmaps",
    desc: "AI-generated sprint-ready modernization plans ranked by effort and impact.",
  },
  {
    icon: Zap,
    title: "Auto-Refactor Previews",
    desc: "See before/after code snippets for every recommendation before applying.",
  },
  {
    icon: Shield,
    title: "Security Intelligence",
    desc: "Cross-repository CVE tracking with remediation steps from AI.",
  },
];

export default function InsightsPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center space-y-10 animate-[fade-in_0.5s_ease-out]">
      <div className="text-center space-y-4">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-accent/10 ring-1 ring-accent/20 mb-6">
          <Bot className="h-10 w-10 text-accent" />
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/5 px-4 py-1.5 text-xs font-medium text-accent">
          <Sparkles className="h-3 w-3" />
          Coming Soon
        </div>
        <h1 className="text-4xl font-bold tracking-tight">AI Insights</h1>
        <p className="max-w-md text-muted-foreground text-sm leading-relaxed">
          AI-powered intelligence across your entire portfolio — not just
          per-repo recommendations, but cross-cutting patterns and priorities.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3 w-full max-w-2xl">
        {PLANNED.map((f) => (
          <div key={f.title} className="glass rounded-xl p-5 space-y-2 opacity-75">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10">
              <f.icon className="h-4 w-4 text-accent" />
            </div>
            <p className="text-sm font-semibold">{f.title}</p>
            <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
