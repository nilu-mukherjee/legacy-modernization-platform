/**
 * @fileoverview Utility functions used throughout the CodeLens AI frontend.
 *
 * Includes:
 * - `cn()` — Tailwind class-name merging (clsx + tailwind-merge)
 * - Number / date / duration formatters
 * - Score-to-colour and score-to-grade helpers
 * - Risk-level → badge-variant mapping
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

import type { RiskLevel, ScoreGrade } from "@/types";

/* ==========================================================================
   Class Name Merging
   ========================================================================== */

/**
 * Merge Tailwind CSS class names intelligently.
 *
 * Combines `clsx` (conditional classes) with `tailwind-merge` (deduplication
 * of conflicting Tailwind utilities like `p-2 p-4` → `p-4`).
 *
 * @param inputs - Class values (strings, arrays, objects, undefined, etc.)
 * @returns Deduplicated, merged class string
 *
 * @example
 * ```ts
 * cn("px-2 py-1", isActive && "bg-primary", className)
 * ```
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/* ==========================================================================
   Number Formatting
   ========================================================================== */

/**
 * Format a number for display with locale-aware separators.
 *
 * @param value - The number to format
 * @param opts  - Intl.NumberFormat options
 * @returns Formatted string (e.g. "12,345")
 */
export function formatNumber(
  value: number,
  opts?: Intl.NumberFormatOptions,
): string {
  return new Intl.NumberFormat("en-US", opts).format(value);
}

/**
 * Format a number as a compact string (e.g. 1.2K, 3.4M).
 *
 * @param value - The number to compact-format
 * @returns Compact string representation
 */
export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

/* ==========================================================================
   Date Formatting
   ========================================================================== */

/**
 * Format an ISO-8601 date string to a human-readable form.
 *
 * @param dateStr - ISO date string (e.g. "2025-01-15T10:30:00Z")
 * @param pattern - date-fns format pattern (default: "MMM d, yyyy")
 * @returns Formatted date string
 */
export function formatDate(
  dateStr: string | null | undefined,
  pattern = "MMM d, yyyy",
): string {
  if (!dateStr) return "—";
  return format(new Date(dateStr), pattern);
}

/**
 * Format a date as a relative string (e.g. "3 hours ago").
 *
 * @param dateStr - ISO date string
 * @returns Relative time string
 */
export function formatRelative(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
}

/* ==========================================================================
   Duration Formatting
   ========================================================================== */

/**
 * Format a duration in hours to a human-readable string.
 *
 * @param hours - Number of hours (can be fractional)
 * @returns Formatted string (e.g. "2h 30m", "45m", "3d 4h")
 */
export function formatDuration(hours: number): string {
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes}m`;
  }
  if (hours < 24) {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
}

/* ==========================================================================
   Score Helpers
   ========================================================================== */

/**
 * Map a modernisation score (0–100) to a Tailwind text-colour class.
 *
 * | Range    | Colour  |
 * |----------|---------|
 * | 80–100   | Emerald |
 * | 60–79    | Lime    |
 * | 40–59    | Amber   |
 * | 20–39    | Orange  |
 * | 0–19     | Rose    |
 *
 * @param score - Score between 0 and 100
 * @returns Tailwind text-colour class
 */
export function getScoreColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-lime-400";
  if (score >= 40) return "text-amber-400";
  if (score >= 20) return "text-orange-400";
  return "text-rose-400";
}

/**
 * Return a hex colour for a given score — useful for SVG / canvas fills.
 *
 * @param score - Score between 0 and 100
 * @returns Hex colour string
 */
export function getScoreHex(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#84cc16";
  if (score >= 40) return "#f59e0b";
  if (score >= 20) return "#f97316";
  return "#f43f5e";
}

/**
 * Map a score (0–100) to a letter grade.
 *
 * @param score - Score between 0 and 100
 * @returns Letter grade: A, B, C, D, or F
 */
export function getScoreGrade(score: number): ScoreGrade {
  if (score >= 80) return "A";
  if (score >= 60) return "B";
  if (score >= 40) return "C";
  if (score >= 20) return "D";
  return "F";
}

/* ==========================================================================
   Risk / Badge Helpers
   ========================================================================== */

/**
 * Map a `RiskLevel` to a badge variant name that matches the `<Badge>` component.
 *
 * @param risk - Risk level
 * @returns Badge variant string
 */
export function getRiskBadgeVariant(
  risk: RiskLevel,
): "destructive" | "warning" | "secondary" | "success" | "outline" {
  const map: Record<RiskLevel, "destructive" | "warning" | "secondary" | "success" | "outline"> = {
    critical: "destructive",
    high: "destructive",
    medium: "warning",
    low: "secondary",
    info: "outline",
  };
  return map[risk];
}

/**
 * Capitalize the first letter of a string.
 *
 * @param str - Input string
 * @returns Capitalized string
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert a snake_case or kebab-case string to Title Case.
 *
 * @param str - Input string (e.g. "code_quality" or "code-quality")
 * @returns Title-cased string (e.g. "Code Quality")
 */
export function toTitleCase(str: string): string {
  return str
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
