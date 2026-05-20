/**
 * @fileoverview Application-wide constants for CodeLens AI.
 *
 * Centralises magic strings and threshold values so they can be tuned
 * from a single location rather than scattered across components.
 */

import {
  Code2,
  Shield,
  Gauge,
  BookOpen,
  TestTube2,
  Layers,
  Wrench,
  type LucideIcon,
} from "lucide-react";

import type { DebtCategory, RiskLevel } from "@/types";

/* ==========================================================================
   Application Identity
   ========================================================================== */

/** Display name shown in the UI header and metadata. */
export const APP_NAME = "CodeLens AI" as const;

/** One-liner tagline used on the landing page. */
export const APP_TAGLINE =
  "AI-Powered Legacy Modernization Platform" as const;

/** Full description for SEO and marketing. */
export const APP_DESCRIPTION =
  "Analyze legacy codebases, identify technical debt, and generate actionable modernization recommendations with AI." as const;

/* ==========================================================================
   Score Thresholds
   ========================================================================== */

/**
 * Boundaries used to map a numeric score (0–100) to a letter grade.
 * Each entry is the *minimum* score for the corresponding grade.
 */
export const SCORE_THRESHOLDS = {
  A: 80,
  B: 60,
  C: 40,
  D: 20,
  F: 0,
} as const;

/* ==========================================================================
   Risk Levels
   ========================================================================== */

/** Ordered risk levels — highest severity first. */
export const RISK_LEVELS: readonly RiskLevel[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
] as const;

/** Human-readable labels for each risk level. */
export const RISK_LABELS: Record<RiskLevel, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  info: "Info",
};

/** Tailwind text-colour classes for each risk level. */
export const RISK_COLORS: Record<RiskLevel, string> = {
  critical: "text-rose-500",
  high: "text-orange-500",
  medium: "text-amber-500",
  low: "text-sky-500",
  info: "text-slate-400",
};

/* ==========================================================================
   Debt Categories
   ========================================================================== */

/** Human-readable labels for debt categories. */
export const CATEGORY_LABELS: Record<DebtCategory, string> = {
  code_quality: "Code Quality",
  architecture: "Architecture",
  security: "Security",
  performance: "Performance",
  maintainability: "Maintainability",
  testing: "Testing",
  documentation: "Documentation",
};

/** Lucide icon component mapped to each debt category. */
export const CATEGORY_ICONS: Record<DebtCategory, LucideIcon> = {
  code_quality: Code2,
  architecture: Layers,
  security: Shield,
  performance: Gauge,
  maintainability: Wrench,
  testing: TestTube2,
  documentation: BookOpen,
};

/* ==========================================================================
   Navigation
   ========================================================================== */

/** Sidebar navigation items. */
export const NAV_ITEMS = [
  { label: "Overview", href: "/", icon: "LayoutDashboard" },
  { label: "Projects", href: "/projects", icon: "FolderKanban" },
  { label: "Settings", href: "/settings", icon: "Settings" },
] as const;

/* ==========================================================================
   Polling
   ========================================================================== */

/** Default interval (ms) for polling job status endpoints. */
export const JOB_POLL_INTERVAL_MS = 3_000;

/** Maximum number of poll attempts before giving up. */
export const JOB_POLL_MAX_ATTEMPTS = 200;

/* ==========================================================================
   Language colours (simplified GitHub-style mapping)
   ========================================================================== */

/** Dot colours shown next to language labels. */
export const LANGUAGE_COLORS: Record<string, string> = {
  TypeScript: "#3178c6",
  JavaScript: "#f7df1e",
  Python: "#3572a5",
  Java: "#b07219",
  Go: "#00add8",
  Rust: "#dea584",
  "C#": "#178600",
  "C++": "#f34b7d",
  Ruby: "#701516",
  PHP: "#4F5D95",
  Swift: "#ffac45",
  Kotlin: "#A97BFF",
  Scala: "#c22d40",
  Shell: "#89e051",
};
