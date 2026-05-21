/**
 * New Project Page
 * ================
 * Form to submit a GitHub repository URL for analysis.
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { GitBranch, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

export default function NewProjectPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/v1/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("codelens_token")}`,
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          name: name || undefined,
        }),
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
          Enter a GitHub repository URL to start the modernization analysis.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-5 glow-border">
        <div>
          <label htmlFor="repo-url" className="block text-sm font-medium mb-2">
            GitHub Repository URL
          </label>
          <div className="relative">
            <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              id="repo-url"
              type="url"
              placeholder="https://github.com/owner/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              required
              className="w-full rounded-lg border border-input bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>

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
          <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !repoUrl}
          className="w-full rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Starting Analysis...
            </>
          ) : (
            "Start Analysis"
          )}
        </button>
      </form>

      <div className="glass rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">What happens next?</h3>
        <ol className="space-y-2 text-sm text-muted-foreground">
          <li className="flex gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">1</span>
            We clone your repository (shallow, read-only)
          </li>
          <li className="flex gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">2</span>
            Parse every source file with AST analysis
          </li>
          <li className="flex gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">3</span>
            Detect technical debt, check dependencies
          </li>
          <li className="flex gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">4</span>
            Generate AI-powered modernization recommendations
          </li>
        </ol>
      </div>
    </div>
  );
}
