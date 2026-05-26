import Link from "next/link";
import {
  GitBranch,
  Shield,
  BarChart3,
  Zap,
  Bot,
  FileCode2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Package,
  Code2,
  Layers,
  Github,
} from "lucide-react";
import { auth } from "@/lib/auth";

const STEPS = [
  {
    n: "01",
    title: "Connect",
    body: "Link any GitHub repository via OAuth. Public or private, any size.",
    icon: Github,
  },
  {
    n: "02",
    title: "Analyze",
    body: "tree-sitter AST parsing + debt rules engine runs across your entire codebase in minutes.",
    icon: Code2,
  },
  {
    n: "03",
    title: "Modernize",
    body: "Claude synthesizes findings into a scored report with prioritized, actionable recommendations.",
    icon: Zap,
  },
];

const FEATURES = [
  {
    icon: Code2,
    title: "AST-Powered Analysis",
    body: "Structural code analysis using tree-sitter — cyclomatic complexity, nesting depth, function length — across Python, JS, TS, and Java.",
  },
  {
    icon: BarChart3,
    title: "Debt Scoring",
    body: "576+ debt patterns across 6 categories with severity levels. Every issue pinpointed to a file and line.",
  },
  {
    icon: Package,
    title: "Dependency Intelligence",
    body: "Version lag, CVE detection, and deprecation alerts from npm, PyPI, and Maven registries.",
  },
  {
    icon: Shield,
    title: "Security Scanning",
    body: "Detects hardcoded secrets, SQL injection patterns, eval() usage, and other critical vulnerabilities.",
  },
  {
    icon: Bot,
    title: "AI Recommendations",
    body: "Claude Sonnet synthesizes all findings into a prioritized modernization roadmap with effort estimates.",
  },
  {
    icon: Layers,
    title: "PDF Reports",
    body: "Export a full analysis report — scores, debt breakdown, dependency risks, and top issues — as a polished PDF.",
  },
];

const SCORE_DIMS = [
  { label: "Code Health",     score: 72,  color: "#22c55e" },
  { label: "Architecture",    score: 100, color: "#22c55e" },
  { label: "Dependencies",    score: 60,  color: "#eab308" },
  { label: "Test Coverage",   score: 31,  color: "#f97316" },
  { label: "Documentation",   score: 70,  color: "#22c55e" },
  { label: "Security",        score: 0,   color: "#ef4444" },
  { label: "Infrastructure",  score: 50,  color: "#eab308" },
];

export default async function LandingPage() {
  const session = await auth();
  const isSignedIn = !!session?.user;

  return (
    <div className="min-h-screen bg-background">

      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 z-50 w-full glass">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
              <FileCode2 className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold">CodeLens AI</span>
          </div>
          <div className="flex items-center gap-4">
            {isSignedIn ? (
              <Link
                href="/dashboard"
                className="rounded-lg gradient-primary px-5 py-2 text-sm font-semibold text-white transition-all hover:opacity-90"
              >
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  Sign In
                </Link>
                <Link
                  href="/login"
                  className="rounded-lg gradient-primary px-5 py-2 text-sm font-semibold text-white transition-all hover:opacity-90 hover:shadow-lg"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="relative flex min-h-screen items-center overflow-hidden px-6 pt-16">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-60 top-0 h-[600px] w-[600px] rounded-full bg-primary/8 blur-[120px]" />
          <div className="absolute -right-40 bottom-0 h-[500px] w-[500px] rounded-full bg-accent/8 blur-[120px]" />
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                "linear-gradient(oklch(0.985 0 0) 1px, transparent 1px), linear-gradient(90deg, oklch(0.985 0 0) 1px, transparent 1px)",
              backgroundSize: "60px 60px",
            }}
          />
        </div>

        <div className="relative z-10 mx-auto grid max-w-7xl gap-16 lg:grid-cols-2 lg:items-center">
          {/* Left: copy */}
          <div className="animate-[fade-in_0.7s_ease-out]">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
              <Zap className="h-3.5 w-3.5" />
              AI-Powered Code Intelligence
            </div>
            <h1 className="mb-6 text-5xl font-extrabold leading-[1.1] tracking-tight lg:text-6xl">
              Legacy codebase.{" "}
              <span className="gradient-text">Clear path forward.</span>
            </h1>
            <p className="mb-8 max-w-lg text-lg leading-relaxed text-muted-foreground">
              Connect a GitHub repository. Get a full technical debt analysis,
              dependency risk report, and AI-generated modernization roadmap —
              in minutes, not weeks.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/login"
                className="group inline-flex items-center gap-2 rounded-xl gradient-primary px-7 py-3.5 text-base font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30"
              >
                Analyze a Repository
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-xl border border-border px-7 py-3.5 text-base font-semibold transition-colors hover:bg-muted"
              >
                How it works
              </Link>
            </div>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
              {["Python", "JavaScript", "TypeScript", "Java"].map((lang) => (
                <span key={lang} className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                  {lang}
                </span>
              ))}
            </div>
          </div>

          {/* Right: mock analysis card */}
          <div className="animate-[slide-up_0.8s_ease-out_0.2s_both]">
            <div className="glass rounded-2xl p-1 glow-border">
              <div className="flex items-center gap-1.5 rounded-t-xl bg-muted/50 px-4 py-3">
                <span className="h-3 w-3 rounded-full bg-destructive/70" />
                <span className="h-3 w-3 rounded-full bg-warning/70" />
                <span className="h-3 w-3 rounded-full bg-success/70" />
                <span className="ml-3 text-xs font-mono text-muted-foreground">
                  codelens — nilustack analysis
                </span>
              </div>

              <div className="p-6 font-mono text-sm">
                <div className="mb-5 space-y-1.5">
                  {[
                    { text: "Cloning repository…",               time: "1.2s" },
                    { text: "Inventoried 242 files, 23,988 LOC", time: "0.4s" },
                    { text: "AST parse complete (Python, TS)",   time: "3.8s" },
                    { text: "576 debt issues detected",          time: "1.1s" },
                    { text: "Dependency scan complete",          time: "2.3s" },
                    { text: "AI synthesis complete",             time: "8.6s" },
                  ].map((line) => (
                    <div key={line.text} className="flex items-center gap-2 text-xs">
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                      <span className="flex-1 text-foreground/80">{line.text}</span>
                      <span className="text-muted-foreground">{line.time}</span>
                    </div>
                  ))}
                </div>

                <div className="rounded-xl border border-border bg-background/50 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground uppercase tracking-wider">Modernization Score</span>
                    <span className="rounded-md bg-warning/15 px-2 py-0.5 text-xs font-bold text-warning">Grade B</span>
                  </div>
                  <div className="mb-4 flex items-end gap-2">
                    <span className="text-4xl font-extrabold text-warning">67</span>
                    <span className="mb-1 text-lg text-muted-foreground">/100</span>
                  </div>
                  <div className="space-y-2">
                    {SCORE_DIMS.map((d) => (
                      <div key={d.label} className="flex items-center gap-3">
                        <span className="w-28 shrink-0 text-[11px] text-muted-foreground">{d.label}</span>
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${d.score}%`, backgroundColor: d.color }}
                          />
                        </div>
                        <span className="w-7 shrink-0 text-right text-[11px]" style={{ color: d.color }}>{d.score}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                  {[
                    { label: "Debt Issues",      value: "576",    color: "text-destructive" },
                    { label: "Dependencies",     value: "3 risks", color: "text-warning" },
                    { label: "Recommendations",  value: "12",     color: "text-primary" },
                  ].map((s) => (
                    <div key={s.label} className="rounded-lg bg-muted/40 px-2 py-2">
                      <div className={`text-base font-bold ${s.color}`}>{s.value}</div>
                      <div className="mt-0.5 text-[10px] text-muted-foreground">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats strip ─────────────────────────────────────────────────── */}
      <section className="border-y border-border py-10">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 px-6 text-center md:grid-cols-4">
          {[
            { value: "4",      label: "Languages supported" },
            { value: "12+",    label: "Debt rule categories" },
            { value: "7",      label: "Score dimensions" },
            { value: "<5 min", label: "Average analysis time" },
          ].map((s) => (
            <div key={s.label}>
              <div className="text-3xl font-extrabold gradient-text">{s.value}</div>
              <div className="mt-1 text-sm text-muted-foreground">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────────────── */}
      <section id="how-it-works" className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="mb-3 text-3xl font-bold md:text-4xl">How it works</h2>
            <p className="text-muted-foreground">Three steps from repo URL to modernization roadmap.</p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.n} className="glass rounded-xl p-6 card-hover">
                <div className="mb-4 flex items-center gap-3">
                  <span className="text-4xl font-extrabold leading-none text-primary/20">{step.n}</span>
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg gradient-primary">
                    <step.icon className="h-4 w-4 text-white" />
                  </div>
                </div>
                <h3 className="mb-2 text-lg font-semibold">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────── */}
      <section id="features" className="border-t border-border px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-14 text-center">
            <h2 className="mb-3 text-3xl font-bold md:text-4xl">Built for engineering teams</h2>
            <p className="mx-auto max-w-xl text-muted-foreground">
              Every layer of the analysis pipeline is designed to give you actionable signal, not noise.
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass rounded-xl p-6 card-hover">
                <div className="mb-4 inline-flex rounded-lg bg-primary/10 p-2.5">
                  <f.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mb-2 font-semibold">{f.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Debt preview ────────────────────────────────────────────────── */}
      <section className="border-t border-border px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="mb-4 text-3xl font-bold leading-tight">
                Every issue,{" "}
                <span className="gradient-text">precisely located</span>
              </h2>
              <p className="mb-6 leading-relaxed text-muted-foreground">
                The debt engine checks 12+ rule categories — complexity,
                architecture, security, documentation — and reports each
                finding with its file path, severity, and description.
              </p>
              <ul className="space-y-3">
                {[
                  "Cyclomatic complexity > 10 → flagged per function",
                  "Hardcoded secrets detected via regex patterns",
                  "God classes with 20+ methods identified",
                  "Missing docstrings on public functions > 10 LOC",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                    <span className="text-muted-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="glass overflow-hidden rounded-xl glow-border">
              <div className="border-b border-border px-4 py-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Top Issues by Severity
              </div>
              <div className="divide-y divide-border">
                {[
                  { sev: "CRITICAL", rule: "HARDCODED_SECRET",   file: "config/settings.py", line: 42 },
                  { sev: "HIGH",     rule: "COMPLEXITY_HIGH",    file: "services/processor.py", line: 187 },
                  { sev: "HIGH",     rule: "GOD_CLASS",          file: "models/legacy_model.py", line: 1 },
                  { sev: "MEDIUM",   rule: "VERY_LONG_FUNCTION", file: "utils/helpers.js", line: 324 },
                  { sev: "MEDIUM",   rule: "DEEP_NESTING",       file: "api/routes/data.py", line: 98 },
                ].map((row) => (
                  <div key={`${row.file}:${row.line}`} className="flex items-center gap-3 px-4 py-2.5 text-xs">
                    <span
                      className={`shrink-0 rounded px-1.5 py-0.5 font-semibold ${
                        row.sev === "CRITICAL"
                          ? "bg-destructive/20 text-destructive"
                          : row.sev === "HIGH"
                          ? "bg-orange-500/20 text-orange-400"
                          : "bg-warning/20 text-warning"
                      }`}
                    >
                      {row.sev}
                    </span>
                    <span className="flex-1 truncate font-mono text-foreground/70">{row.rule}</span>
                    <span className="shrink-0 font-mono text-muted-foreground">
                      {row.file}:{row.line}
                    </span>
                  </div>
                ))}
              </div>
              <div className="border-t border-border px-4 py-2.5 text-xs text-muted-foreground">
                + 571 more issues
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="border-t border-border px-6 py-24">
        <div className="mx-auto max-w-3xl text-center">
          <div className="glass rounded-2xl p-12 glow-border">
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <GitBranch className="h-3 w-3" />
              GitHub OAuth — no setup required
            </div>
            <h2 className="mb-3 mt-4 text-3xl font-bold">Start your first analysis</h2>
            <p className="mb-8 text-muted-foreground">
              Sign in with GitHub, paste a repo URL, and get your modernization score in under 5 minutes.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl gradient-primary px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl"
            >
              Get Started — It&apos;s Free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-border px-6 py-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileCode2 className="h-4 w-4" />
            <span>CodeLens AI</span>
          </div>
          <div className="text-sm text-muted-foreground">
            AGPL-3.0 License · Built for HyKr Build Challenge 2026
          </div>
        </div>
      </footer>
    </div>
  );
}
