/**
 * @fileoverview Centralised TypeScript type definitions for CodeLens AI.
 *
 * Every interface in this file maps 1-to-1 with the backend API schemas
 * so the frontend can safely serialize / deserialize JSON payloads.
 *
 * Convention: exported types use PascalCase, enum-like unions use
 * SCREAMING_SNAKE_CASE values for API compatibility.
 */

/* ==========================================================================
   Enums / Union Literals
   ========================================================================== */

/** Possible statuses for an analysis job. */
export type AnalysisStatus =
  | "pending"
  | "cloning"
  | "analyzing"
  | "scoring"
  | "generating_recommendations"
  | "completed"
  | "failed";

/** Category of a technical-debt finding. */
export type DebtCategory =
  | "code_quality"
  | "architecture"
  | "security"
  | "performance"
  | "maintainability"
  | "testing"
  | "documentation";

/** Severity / risk level used across the platform. */
export type RiskLevel = "critical" | "high" | "medium" | "low" | "info";

/** Letter grade for a modernisation score. */
export type ScoreGrade = "A" | "B" | "C" | "D" | "F";

/** Supported export formats for reports. */
export type ReportFormat = "pdf" | "json" | "markdown";

/* ==========================================================================
   Core Domain Models
   ========================================================================== */

/** Authenticated user profile. */
export interface User {
  /** Internal UUID. */
  id: string;
  /** Display name (from GitHub). */
  name: string;
  /** Primary email. */
  email: string;
  /** URL to the user's avatar image. */
  avatarUrl: string;
  /** GitHub username. */
  githubUsername: string;
}

/** Top-level project entity — wraps a repository analysis. */
export interface Project {
  id: string;
  name: string;
  description: string;
  repoUrl: string;
  defaultBranch: string;
  language: string;
  languages: string[];
  status: AnalysisStatus;
  /** Aggregate modernisation score (0–100). */
  score: number | null;
  /** ISO-8601 timestamp of last completed analysis. */
  lastAnalyzedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Detailed analysis result produced by the backend. */
export interface Analysis {
  id: string;
  projectId: string;
  status: AnalysisStatus;
  /** Overall lines of code counted. */
  totalLoc: number;
  /** Number of files scanned. */
  totalFiles: number;
  /** Total technical-debt items found. */
  totalDebtItems: number;
  /** Estimated person-hours to resolve all debt. */
  estimatedHours: number;
  /** ISO-8601 timestamps. */
  startedAt: string;
  completedAt: string | null;
}

/** Per-file metrics produced by the analysis engine. */
export interface FileMetric {
  filePath: string;
  language: string;
  loc: number;
  complexity: number;
  maintainabilityIndex: number;
  duplicatePercentage: number;
  testCoverage: number | null;
  issues: number;
}

/** A single technical-debt item. */
export interface DebtItem {
  id: string;
  title: string;
  description: string;
  category: DebtCategory;
  severity: RiskLevel;
  filePath: string;
  lineStart: number;
  lineEnd: number;
  estimatedHours: number;
  suggestion: string;
}

/** A dependency-level finding (outdated, vulnerable, etc.). */
export interface DependencyFinding {
  id: string;
  packageName: string;
  currentVersion: string;
  latestVersion: string;
  /** Days between current and latest release. */
  daysBehind: number;
  riskLevel: RiskLevel;
  /** Number of known vulnerabilities. */
  vulnerabilities: number;
  /** CVE identifiers, if any. */
  cveIds: string[];
  /** Whether a direct or transitive dependency. */
  isDirect: boolean;
}

/** AI-generated modernisation recommendation. */
export interface Recommendation {
  id: string;
  analysisId: string;
  title: string;
  description: string;
  rationale: string;
  category: DebtCategory;
  priority: RiskLevel;
  estimatedHours: number;
  impactScore: number;
  implementationSteps: string[];
  /** Whether the user has requested an AI refactoring for this rec. */
  refactoringRequested: boolean;
  refactoringJobId: string | null;
}

/** Aggregated modernisation score with sub-dimensions. */
export interface ModernizationScore {
  overall: number;
  grade: ScoreGrade;
  dimensions: ScoreDimension[];
}

/** A single dimension within the score radar. */
export interface ScoreDimension {
  name: string;
  score: number;
  maxScore: number;
  description: string;
}

/* ==========================================================================
   Job / Progress Tracking
   ========================================================================== */

/** Background job (analysis, refactoring, etc.). */
export interface Job {
  id: string;
  type: "analysis" | "refactoring" | "report";
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  currentStep: string;
  steps: JobStep[];
  createdAt: string;
  completedAt: string | null;
  error: string | null;
}

/** Individual step within a job. */
export interface JobStep {
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  startedAt: string | null;
  completedAt: string | null;
}

/* ==========================================================================
   Reports
   ========================================================================== */

/** Complete report data returned by the backend. */
export interface ReportData {
  projectId: string;
  projectName: string;
  generatedAt: string;
  score: ModernizationScore;
  analysis: Analysis;
  topDebtItems: DebtItem[];
  topRecommendations: Recommendation[];
  dependencySummary: {
    total: number;
    outdated: number;
    vulnerable: number;
    critical: number;
  };
}

/* ==========================================================================
   API Response Wrappers
   ========================================================================== */

/** Standard paginated list response. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/** Standard API error response. */
export interface ApiError {
  statusCode: number;
  message: string;
  details?: string;
}

/** Generic single-item API response. */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

/* ==========================================================================
   File Tree (for structure visualization)
   ========================================================================== */

/** Recursive node in a repository file-tree. */
export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  language?: string;
  children?: FileTreeNode[];
  metrics?: FileMetric;
}

/* ==========================================================================
   Dashboard-specific view models
   ========================================================================== */

/** Stats card data for the overview page. */
export interface DashboardStats {
  totalProjects: number;
  averageScore: number;
  criticalIssues: number;
  reposAnalyzed: number;
}
