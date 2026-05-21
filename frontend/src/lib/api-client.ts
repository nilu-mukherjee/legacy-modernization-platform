/**
 * API Client
 * ==========
 * Typed HTTP client for communicating with the FastAPI backend.
 * All API calls go through this module.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generic fetch wrapper with auth token injection and error handling.
 */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Inject auth token from localStorage if available.
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("codelens_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────

export async function syncUser(payload: {
  github_id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  access_token: string;
}) {
  return apiFetch<{ id: string; token: string }>("/api/v1/auth/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMe() {
  return apiFetch<{ id: string; email: string; name: string }>("/api/v1/auth/me");
}

// ── Projects ──────────────────────────────────────────────────────────────

export async function listProjects(skip = 0, limit = 20) {
  return apiFetch<{ projects: any[]; total: number }>(
    `/api/v1/projects?skip=${skip}&limit=${limit}`
  );
}

export async function createProject(repoUrl: string, name?: string) {
  return apiFetch<{ id: string; job_id: string }>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify({ repo_url: repoUrl, name }),
  });
}

export async function getProject(projectId: string) {
  return apiFetch<any>(`/api/v1/projects/${projectId}`);
}

export async function deleteProject(projectId: string) {
  return apiFetch<void>(`/api/v1/projects/${projectId}`, { method: "DELETE" });
}

export async function reAnalyze(projectId: string) {
  return apiFetch<{ job_id: string }>(`/api/v1/projects/${projectId}/analyze`, {
    method: "POST",
  });
}

// ── Analysis ──────────────────────────────────────────────────────────────

export async function getAnalysis(projectId: string) {
  return apiFetch<any>(`/api/v1/projects/${projectId}/analysis`);
}

export async function getScore(projectId: string) {
  return apiFetch<any>(`/api/v1/projects/${projectId}/analysis/score`);
}

export async function getFileMetrics(projectId: string, skip = 0, limit = 50) {
  return apiFetch<{ files: any[]; total: number }>(
    `/api/v1/projects/${projectId}/analysis/files?skip=${skip}&limit=${limit}`
  );
}

export async function getDebtItems(projectId: string) {
  return apiFetch<{ debt_items: any[]; total: number; by_severity: Record<string, number> }>(
    `/api/v1/projects/${projectId}/analysis/debt`
  );
}

export async function getDependencies(projectId: string) {
  return apiFetch<{ dependencies: any[]; total: number; summary: any }>(
    `/api/v1/projects/${projectId}/analysis/dependencies`
  );
}

// ── Recommendations ───────────────────────────────────────────────────────

export async function getRecommendations(projectId: string) {
  return apiFetch<{ recommendations: any[]; total: number }>(
    `/api/v1/projects/${projectId}/recommendations`
  );
}

export async function refactorRecommendation(projectId: string, recId: string) {
  return apiFetch<{ before_code: string; after_code: string; explanation: string }>(
    `/api/v1/projects/${projectId}/recommendations/${recId}/refactor`,
    { method: "POST" }
  );
}

// ── Jobs ──────────────────────────────────────────────────────────────────

export async function getJob(jobId: string) {
  return apiFetch<{
    id: string;
    status: string;
    progress: number;
    current_step: string;
    steps: { name: string; status: string }[];
  }>(`/api/v1/jobs/${jobId}`);
}

// ── Reports ───────────────────────────────────────────────────────────────

export async function getReport(projectId: string) {
  return apiFetch<any>(`/api/v1/projects/${projectId}/report`);
}
