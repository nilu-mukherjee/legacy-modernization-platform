"use client";

import { useState, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { GitBranch, ArrowLeft, Loader2, Search, Star, Lock, ChevronDown, X, Sparkles } from "lucide-react";
import Link from "next/link";

const SAMPLE_REPOS: { url: string; label: string; description: string; language: string }[] = [
  {
    url: "https://github.com/sindresorhus/normalize-url",
    label: "normalize-url",
    description: "Tiny JS utility — quick analysis (~30s)",
    language: "TypeScript",
  },
  {
    url: "https://github.com/pallets/flask",
    label: "pallets/flask",
    description: "Popular Python web framework — rich findings",
    language: "Python",
  },
  {
    url: "https://github.com/expressjs/express",
    label: "expressjs/express",
    description: "Node.js framework — multi-language analysis",
    language: "JavaScript",
  },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface GhRepo {
  id: number;
  full_name: string;
  html_url: string;
  description: string | null;
  private: boolean;
  stargazers_count: number;
  language: string | null;
  updated_at: string;
}

export default function NewProjectPage() {
  const [repos, setRepos] = useState<GhRepo[]>([]);
  const [reposLoading, setReposLoading] = useState(true);
  const [reposError, setReposError] = useState("");

  const [selected, setSelected] = useState<GhRepo | null>(null);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [manualUrl, setManualUrl] = useState("");

  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { data: session, status } = useSession();
  const accessToken = (session as any)?.accessToken as string | undefined;
  const backendToken = (session as any)?.backendToken as string | undefined;

  // Fetch GitHub repos once session is authenticated
  useEffect(() => {
    if (status !== "authenticated") return;
    if (!accessToken) {
      setReposError("no_token");
      setReposLoading(false);
      return;
    }
    setReposLoading(true);
    fetch("https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator", {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setRepos(data);
        } else if (Array.isArray(data) && data.length === 0) {
          setRepos([]);
        } else {
          setReposError("api_error");
        }
      })
      .catch(() => setReposError("api_error"))
      .finally(() => setReposLoading(false));
  }, [status, accessToken]);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filtered = repos.filter((r) =>
    r.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (r.description ?? "").toLowerCase().includes(search.toLowerCase())
  );

  function selectRepo(repo: GhRepo) {
    setSelected(repo);
    setName(repo.full_name.split("/")[1]);
    setOpen(false);
    setSearch("");
  }

  function clearSelection() {
    setSelected(null);
    setName("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const repoUrl = selected?.html_url || manualUrl.trim();
    if (!repoUrl) return;
    await startAnalysis(repoUrl, name || undefined);
  }

  async function startAnalysis(repoUrl: string, projectName?: string) {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${backendToken}`,
        },
        body: JSON.stringify({ repo_url: repoUrl, name: projectName }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create project");
      }
      const data = await res.json();
      router.push(`/dashboard/projects/${data.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSampleClick(repoUrl: string, label: string) {
    if (loading) return;
    await startAnalysis(repoUrl, label);
  }

  return (
    <div className="mx-auto max-w-lg space-y-6 animate-[fade-in_0.5s_ease-out]">
      <div>
        <Link
          href="/dashboard/projects"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Projects
        </Link>
        <h1 className="text-2xl font-bold">Analyze a Repository</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pick a GitHub repository to start the modernization analysis.
        </p>
      </div>

      {/* Sample repos — quick start for evaluators / first-time users */}
      <div className="glass rounded-xl p-5 border border-primary/20">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">Try with a sample repo</h3>
          <span className="text-xs text-muted-foreground">— no setup needed</span>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          {SAMPLE_REPOS.map((s) => (
            <button
              key={s.url}
              type="button"
              onClick={() => handleSampleClick(s.url, s.label)}
              disabled={loading}
              style={{ cursor: loading ? "default" : "pointer" }}
              className="text-left rounded-lg border border-border bg-background/50 px-3 py-2.5 hover:border-primary hover:bg-primary/5 transition-all disabled:opacity-50"
            >
              <div className="flex items-center gap-1.5">
                <GitBranch className="h-3.5 w-3.5 text-primary shrink-0" />
                <span className="text-sm font-medium truncate">{s.label}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{s.description}</p>
              <span className="mt-1 inline-block text-[10px] text-muted-foreground/70">{s.language}</span>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-5 glow-border">
        {/* Repo picker */}
        <div>
          <label className="block text-sm font-medium mb-2">GitHub Repository</label>

          {reposError ? (
            <div className="space-y-3">
              <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {reposError === "no_token"
                  ? "GitHub access token not available. Paste the repository URL manually."
                  : "Could not load repositories. Paste the repository URL manually."}
              </div>
              <input
                type="url"
                placeholder="https://github.com/owner/repo"
                value={manualUrl}
                onChange={(e) => setManualUrl(e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          ) : (
            <div ref={dropdownRef} className="relative">
              {/* Trigger */}
              <button
                type="button"
                onClick={() => !reposLoading && setOpen((o) => !o)}
                className="w-full flex items-center justify-between gap-2 rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
                disabled={reposLoading}
              >
                {reposLoading ? (
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" /> Loading repositories…
                  </span>
                ) : selected ? (
                  <span className="flex items-center gap-2 min-w-0">
                    <GitBranch className="h-4 w-4 text-primary shrink-0" />
                    <span className="truncate font-medium">{selected.full_name}</span>
                    {selected.private && <Lock className="h-3 w-3 text-muted-foreground shrink-0" />}
                  </span>
                ) : (
                  <span className="text-muted-foreground">Select a repository…</span>
                )}
                <span className="flex items-center gap-1 shrink-0">
                  {selected && (
                    <span
                      role="button"
                      onClick={(e) => { e.stopPropagation(); clearSelection(); }}
                      className="rounded p-0.5 hover:bg-muted"
                    >
                      <X className="h-3.5 w-3.5 text-muted-foreground" />
                    </span>
                  )}
                  <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
                </span>
              </button>

              {/* Dropdown */}
              {open && (
                <div className="absolute z-50 mt-1 w-full rounded-xl border border-border bg-background shadow-xl">
                  {/* Search */}
                  <div className="flex items-center gap-2 border-b border-border px-3 py-2">
                    <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <input
                      autoFocus
                      type="text"
                      placeholder="Search repositories…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="flex-1 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none"
                    />
                  </div>

                  {/* List */}
                  <ul className="max-h-64 overflow-y-auto py-1">
                    {filtered.length === 0 ? (
                      <li className="px-4 py-6 text-center text-sm text-muted-foreground">No repositories found</li>
                    ) : (
                      filtered.map((repo) => (
                        <li key={repo.id}>
                          <button
                            type="button"
                            onClick={() => selectRepo(repo)}
                            className="w-full flex items-start gap-3 px-3 py-2.5 text-left hover:bg-muted transition-colors"
                          >
                            <GitBranch className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 min-w-0">
                                <span className="text-sm font-medium truncate">{repo.full_name}</span>
                                {repo.private && <Lock className="h-3 w-3 text-muted-foreground shrink-0" />}
                              </div>
                              {repo.description && (
                                <p className="text-xs text-muted-foreground truncate mt-0.5">{repo.description}</p>
                              )}
                              <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                {repo.language && <span>{repo.language}</span>}
                                {repo.stargazers_count > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Star className="h-3 w-3" />{repo.stargazers_count}
                                  </span>
                                )}
                              </div>
                            </div>
                          </button>
                        </li>
                      ))
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Project name */}
        <div>
          <label htmlFor="project-name" className="block text-sm font-medium mb-2">
            Project Name <span className="text-muted-foreground">(optional)</span>
          </label>
          <input
            id="project-name"
            type="text"
            placeholder="My Legacy App"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        {error && (
          <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
        )}

        <button
          type="submit"
          disabled={loading || (!selected && !manualUrl.trim())}
          className="w-full rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Starting Analysis…
            </>
          ) : (
            "Start Analysis"
          )}
        </button>
      </form>

      <div className="glass rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">What happens next?</h3>
        <ol className="space-y-2 text-sm text-muted-foreground">
          {[
            "We clone your repository (shallow, read-only)",
            "Parse every source file with AST analysis",
            "Detect technical debt, check dependencies",
            "Generate AI-powered modernization recommendations",
          ].map((step, i) => (
            <li key={i} className="flex gap-2">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
