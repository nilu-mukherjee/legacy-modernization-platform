"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  MoreVertical,
  Trash2,
  FileDown,
  X,
} from "lucide-react";
import { listProjects, deleteProject, setAuthToken } from "@/lib/api-client";
import { downloadReport } from "@/lib/download-report";
import { useSession } from "next-auth/react";
import { Pagination } from "@/components/ui/pagination";

const LANG_COLORS: Record<string, string> = {
  python: "#3572A5", javascript: "#f1e05a", typescript: "#2b7489",
  java: "#b07219", go: "#00ADD8", rust: "#dea584", ruby: "#701516",
  csharp: "#178600", cpp: "#f34b7d", c: "#555555", php: "#4F5D95",
  swift: "#F05138", kotlin: "#A97BFF", scala: "#c22d40", dart: "#00B4AB",
  shell: "#89e051", html: "#e34c26", css: "#563d7c", sql: "#e38c00",
};

function getLangColor(lang: string): string {
  return LANG_COLORS[lang.toLowerCase()] ?? "#8b8b8b";
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true })
  );
}

function statusDisplay(status: string) {
  switch (status) {
    case "completed":
      return { icon: CheckCircle2, label: "Completed", color: "text-green-500" };
    case "analyzing":
      return { icon: Loader2, label: "Analyzing", color: "text-primary", spin: true };
    case "failed":
      return { icon: AlertCircle, label: "Failed", color: "text-destructive" };
    default:
      return { icon: Clock, label: "Pending", color: "text-muted-foreground" };
  }
}

export default function ProjectsPage() {
  const { data: session, status } = useSession();
  const [projects, setProjects] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 12;
  const [loading, setLoading] = useState(true);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<any | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = (session as any)?.backendToken as string | undefined;
    setAuthToken(token ?? null);
    setLoading(true);
    listProjects((page - 1) * PAGE_SIZE, PAGE_SIZE)
      .then((res) => {
        setProjects(res.projects);
        setTotal(res.total ?? res.projects.length);
      })
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [status, session, page]);


  async function handleDelete() {
    if (!confirmDelete) return;
    setDeleteLoading(true);
    try {
      await deleteProject(confirmDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== confirmDelete.id));
      setConfirmDelete(null);
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-[fade-in_0.5s_ease-out]">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your repository analyses
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

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : projects.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <FolderGit2 className="h-8 w-8 text-primary" />
          </div>
          <h3 className="mb-2 text-xl font-semibold">No projects yet</h3>
          <p className="mb-6 text-muted-foreground">
            Add a GitHub repository to start analyzing.
          </p>
          <Link
            href="/dashboard/projects/new"
            className="inline-flex items-center gap-2 rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white"
          >
            <Plus className="h-4 w-4" />
            Add Repository
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => {
            const { icon: Icon, label, color, spin } = statusDisplay(project.status) as any;
            const isOpen = menuOpenId === project.id;
            const isAnalyzing = project.status === "analyzing";
            return (
              <div
                key={project.id}
                className={`relative flex glass rounded-xl transition-all hover:glow-border hover:-translate-y-0.5${downloadingId === project.id ? " pointer-events-none" : ""}`}
              >
                {/* Generating report overlay */}
                {downloadingId === project.id && (
                  <div className="absolute inset-0 z-10 flex items-center justify-center gap-2.5 rounded-xl bg-background/80 backdrop-blur-sm">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <span className="text-sm font-medium text-foreground">Generating Report...</span>
                  </div>
                )}
                {/* Main clickable area */}
                <Link href={`/dashboard/projects/${project.id}`} className="flex-1 min-w-0 p-5">
                  <div className="flex items-center gap-2 mb-3 min-w-0">
                    <FolderGit2 className="h-5 w-5 text-primary shrink-0" />
                    <span className="font-semibold truncate">{project.name}</span>
                  </div>

                  {project.repo_full_name && (
                    <p className="text-xs text-muted-foreground font-mono truncate mb-3">
                      {project.repo_full_name}
                    </p>
                  )}

                  {/* Row 1: status · files · LOC · date/time right */}
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className={`flex items-center gap-1 font-medium ${color}`}>
                        <Icon className={`h-3.5 w-3.5${spin ? " animate-spin" : ""}`} />
                        {label}
                      </span>
                      {isAnalyzing ? (
                        <>
                          <span className="h-3 w-14 rounded bg-muted animate-pulse" />
                          <span className="h-3 w-16 rounded bg-muted animate-pulse" />
                        </>
                      ) : (
                        <>
                          {project.total_files > 0 && (
                            <span>{project.total_files.toLocaleString()} files</span>
                          )}
                          {project.total_loc > 0 && (
                            <span>{project.total_loc.toLocaleString()} LOC</span>
                          )}
                        </>
                      )}
                    </div>
                    {project.created_at && (
                      <span className="shrink-0 inline-flex items-center rounded-lg bg-indigo-500/10 px-2 py-1 text-[10px] font-medium text-indigo-400 ring-1 ring-inset ring-indigo-500/20 whitespace-nowrap">
                        {formatDateTime(project.created_at)}
                      </span>
                    )}
                  </div>

                  {/* Row 2: language tags */}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    {isAnalyzing ? (
                      <>
                        <span className="h-3 w-20 rounded bg-muted animate-pulse" />
                        <span className="h-3 w-16 rounded bg-muted animate-pulse" />
                      </>
                    ) : (
                      project.detected_languages &&
                      Object.keys(project.detected_languages).length > 0 &&
                      (() => {
                        const entries = Object.entries(
                          project.detected_languages as Record<string, number>
                        ).sort(([, a], [, b]) => b - a);
                        const total = entries.reduce((s, [, n]) => s + n, 0);
                        return entries.slice(0, 3).map(([lang, count]) => {
                          const pct = total > 0 ? Math.round((count / total) * 1000) / 10 : 0;
                          return (
                            <div key={lang} className="flex items-center gap-1 text-xs">
                              <span
                                className="h-2 w-2 rounded-full shrink-0"
                                style={{ backgroundColor: getLangColor(lang) }}
                              />
                              <span className="font-medium capitalize text-foreground/80">{lang}</span>
                              <span className="text-muted-foreground">{pct}%</span>
                            </div>
                          );
                        });
                      })()
                    )}
                  </div>
                </Link>

                {/* Three-dot menu — hidden while analyzing */}
                <div className="relative flex shrink-0 items-start pt-3 pr-3">
                  {!isAnalyzing && (
                  <button
                    onClick={() => setMenuOpenId(isOpen ? null : project.id)}
                    style={{ cursor: "pointer" }}
                    className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>
                  )}

                  {isOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setMenuOpenId(null)}
                      />
                      <div className="absolute right-0 top-9 z-50 w-48 rounded-xl border border-border bg-background shadow-2xl py-1 overflow-hidden">
                        <button
                          disabled={downloadingId === project.id}
                          onClick={async () => {
                            setMenuOpenId(null);
                            setDownloadingId(project.id);
                            setDownloadError(null);
                            try {
                              await downloadReport(project.id);
                            } catch (err: any) {
                              setDownloadError(err?.message ?? "Failed to generate report.");
                            } finally {
                              setDownloadingId(null);
                            }
                          }}
                          style={{ cursor: downloadingId === project.id ? "wait" : "pointer" }}
                          className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-sm hover:bg-muted transition-colors disabled:opacity-60"
                        >
                          {downloadingId === project.id ? (
                            <Loader2 className="h-4 w-4 text-primary shrink-0 animate-spin" />
                          ) : (
                            <FileDown className="h-4 w-4 text-primary shrink-0" />
                          )}
                          {downloadingId === project.id ? "Generating…" : "Download Report"}
                        </button>
                        <div className="h-px bg-border mx-2 my-1" />
                        <button
                          onClick={() => {
                            setMenuOpenId(null);
                            setConfirmDelete(project);
                          }}
                          style={{ cursor: "pointer" }}
                          className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                        >
                          <Trash2 className="h-4 w-4 shrink-0" />
                          Delete Project
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {total > PAGE_SIZE && (
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          onChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: "smooth" }); }}
        />
      )}

      {/* Download error toast */}
      {downloadError && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-destructive text-destructive-foreground px-5 py-3 rounded-xl shadow-xl text-sm font-medium">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {downloadError}
          <button onClick={() => setDownloadError(null)} className="ml-2 opacity-70 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => !deleteLoading && setConfirmDelete(null)}
          />
          <div className="relative glass rounded-2xl p-6 w-full max-w-sm shadow-2xl glow-border animate-[fade-in_0.15s_ease-out]">
            <button
              onClick={() => !deleteLoading && setConfirmDelete(null)}
              disabled={deleteLoading}
              className="absolute top-4 right-4 rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-destructive/10">
              <Trash2 className="h-6 w-6 text-destructive" />
            </div>

            <h3 className="text-lg font-semibold mb-1">Delete Project</h3>
            <p className="text-sm text-muted-foreground mb-5">
              <span className="font-medium text-foreground">{confirmDelete.name}</span> and all its
              analysis data will be permanently deleted. This cannot be undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                disabled={deleteLoading}
                className="flex-1 rounded-xl border border-border px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="flex-1 rounded-xl bg-destructive px-4 py-2.5 text-sm font-semibold text-white hover:bg-destructive/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {deleteLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
