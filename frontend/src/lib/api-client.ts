/**
 * @fileoverview Typed HTTP client for the CodeLens AI backend API.
 *
 * Usage:
 * ```ts
 * import { api } from "@/lib/api-client";
 * const projects = await api.getProjects();
 * ```
 *
 * All methods are fully typed with generics so callers receive concrete
 * return types without manual casting.
 */

import type {
  Project,
  Analysis,
  ModernizationScore,
  FileMetric,
  DebtItem,
  DependencyFinding,
  Recommendation,
  Job,
  ReportData,
  PaginatedResponse,
  ApiResponse,
  ReportFormat,
} from "@/types";

/* ==========================================================================
   Configuration
   ========================================================================== */

/** Base URL for all API requests — falls back to localhost during development. */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/* ==========================================================================
   ApiClient Class
   ========================================================================== */

/**
 * Typed REST client for the CodeLens AI backend.
 *
 * Wraps `fetch` with:
 * - Automatic JSON serialisation / deserialisation
 * - Auth-token injection (via header)
 * - Centralised error handling
 *
 * Each domain method (e.g. `getProjects()`) returns a strongly-typed Promise.
 */
class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /* ── Auth ──────────────────────────────────────────────────────────── */

  /**
   * Set the bearer token for subsequent requests.
   *
   * @param token - OAuth access token
   */
  setToken(token: string): void {
    this.token = token;
  }

  /**
   * Clear the stored token (e.g. on sign-out).
   */
  clearToken(): void {
    this.token = null;
  }

  /* ── Generic HTTP helpers ──────────────────────────────────────────── */

  /**
   * Build a headers object, injecting the auth token when present.
   */
  private headers(): HeadersInit {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.token) {
      h["Authorization"] = `Bearer ${this.token}`;
    }
    return h;
  }

  /**
   * Execute a fetch request and return parsed JSON.
   *
   * @param method - HTTP method
   * @param path   - URL path appended to `baseUrl`
   * @param body   - Optional request body (will be JSON-stringified)
   * @returns Parsed response of type `T`
   * @throws Error on non-2xx responses
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    const res = await fetch(url, {
      method,
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(
        `API ${method} ${path} failed (${res.status}): ${errorBody}`,
      );
    }

    // Handle 204 No Content
    if (res.status === 204) {
      return undefined as T;
    }

    return res.json() as Promise<T>;
  }

  /** Type-safe GET request. */
  async get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  /** Type-safe POST request. */
  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  /** Type-safe DELETE request. */
  async delete<T>(path: string): Promise<T> {
    return this.request<T>("DELETE", path);
  }

  /* ── Projects ──────────────────────────────────────────────────────── */

  /**
   * List all projects for the authenticated user.
   * @returns Paginated list of projects
   */
  async getProjects(): Promise<PaginatedResponse<Project>> {
    return this.get<PaginatedResponse<Project>>("/api/v1/projects");
  }

  /**
   * Create a new project (triggers analysis).
   *
   * @param data - Repo URL and optional name
   * @returns The created project with an initial analysis job
   */
  async createProject(data: {
    repoUrl: string;
    name?: string;
  }): Promise<ApiResponse<Project>> {
    return this.post<ApiResponse<Project>>("/api/v1/projects", data);
  }

  /**
   * Fetch a single project by ID.
   *
   * @param id - Project UUID
   */
  async getProject(id: string): Promise<ApiResponse<Project>> {
    return this.get<ApiResponse<Project>>(`/api/v1/projects/${id}`);
  }

  /**
   * Delete a project.
   *
   * @param id - Project UUID
   */
  async deleteProject(id: string): Promise<void> {
    return this.delete<void>(`/api/v1/projects/${id}`);
  }

  /* ── Analysis ──────────────────────────────────────────────────────── */

  /**
   * Get the latest analysis for a project.
   *
   * @param projectId - Project UUID
   */
  async getAnalysis(projectId: string): Promise<ApiResponse<Analysis>> {
    return this.get<ApiResponse<Analysis>>(
      `/api/v1/projects/${projectId}/analysis`,
    );
  }

  /* ── Scores ────────────────────────────────────────────────────────── */

  /**
   * Get the modernisation score breakdown.
   *
   * @param projectId - Project UUID
   */
  async getScore(
    projectId: string,
  ): Promise<ApiResponse<ModernizationScore>> {
    return this.get<ApiResponse<ModernizationScore>>(
      `/api/v1/projects/${projectId}/score`,
    );
  }

  /* ── File Metrics ──────────────────────────────────────────────────── */

  /**
   * Get per-file metrics for a project.
   *
   * @param projectId - Project UUID
   */
  async getFileMetrics(
    projectId: string,
  ): Promise<ApiResponse<FileMetric[]>> {
    return this.get<ApiResponse<FileMetric[]>>(
      `/api/v1/projects/${projectId}/files`,
    );
  }

  /* ── Debt Items ────────────────────────────────────────────────────── */

  /**
   * Get all technical-debt items for a project.
   *
   * @param projectId - Project UUID
   */
  async getDebtItems(
    projectId: string,
  ): Promise<PaginatedResponse<DebtItem>> {
    return this.get<PaginatedResponse<DebtItem>>(
      `/api/v1/projects/${projectId}/debt`,
    );
  }

  /* ── Dependencies ──────────────────────────────────────────────────── */

  /**
   * Get dependency findings for a project.
   *
   * @param projectId - Project UUID
   */
  async getDependencies(
    projectId: string,
  ): Promise<PaginatedResponse<DependencyFinding>> {
    return this.get<PaginatedResponse<DependencyFinding>>(
      `/api/v1/projects/${projectId}/dependencies`,
    );
  }

  /* ── Recommendations ───────────────────────────────────────────────── */

  /**
   * Get AI-generated recommendations for a project.
   *
   * @param projectId - Project UUID
   */
  async getRecommendations(
    projectId: string,
  ): Promise<ApiResponse<Recommendation[]>> {
    return this.get<ApiResponse<Recommendation[]>>(
      `/api/v1/projects/${projectId}/recommendations`,
    );
  }

  /**
   * Request an AI-generated refactoring for a specific recommendation.
   *
   * @param projectId - Project UUID
   * @param recId     - Recommendation UUID
   * @returns Job tracking object
   */
  async requestRefactoring(
    projectId: string,
    recId: string,
  ): Promise<ApiResponse<Job>> {
    return this.post<ApiResponse<Job>>(
      `/api/v1/projects/${projectId}/recommendations/${recId}/refactor`,
    );
  }

  /* ── Jobs ──────────────────────────────────────────────────────────── */

  /**
   * Poll for the status of a background job.
   *
   * @param jobId - Job UUID
   */
  async getJobStatus(jobId: string): Promise<ApiResponse<Job>> {
    return this.get<ApiResponse<Job>>(`/api/v1/jobs/${jobId}`);
  }

  /* ── Reports ───────────────────────────────────────────────────────── */

  /**
   * Get the full report data for a project.
   *
   * @param projectId - Project UUID
   */
  async getReport(projectId: string): Promise<ApiResponse<ReportData>> {
    return this.get<ApiResponse<ReportData>>(
      `/api/v1/projects/${projectId}/report`,
    );
  }

  /**
   * Export a report in the specified format.
   *
   * @param projectId - Project UUID
   * @param format    - Export format
   * @returns Blob download URL
   */
  async exportReport(
    projectId: string,
    format: ReportFormat,
  ): Promise<Blob> {
    const url = `${this.baseUrl}/api/v1/projects/${projectId}/report/export?format=${format}`;
    const res = await fetch(url, { headers: this.headers() });

    if (!res.ok) {
      throw new Error(`Export failed (${res.status})`);
    }

    return res.blob();
  }
}

/* ==========================================================================
   Singleton Export
   ========================================================================== */

/**
 * Pre-configured singleton API client instance.
 *
 * Import this across the app:
 * ```ts
 * import { api } from "@/lib/api-client";
 * ```
 */
export const api = new ApiClient(BASE_URL);
