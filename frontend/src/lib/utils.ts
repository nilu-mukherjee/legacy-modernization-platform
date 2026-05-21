/**
 * Utility Functions
 * =================
 * Core utilities used throughout the frontend.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with proper conflict resolution.
 * Combines `clsx` (conditional classes) with `tailwind-merge` (deduplication).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as a compact string (e.g. 1200 → "1.2K").
 */
export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

/**
 * Get the CSS color class for a modernization grade.
 */
export function gradeColor(grade: string): string {
  switch (grade) {
    case "A": return "text-success";
    case "B": return "text-green-400";
    case "C": return "text-warning";
    case "D": return "text-orange-400";
    case "F": return "text-destructive";
    default: return "text-muted-foreground";
  }
}

/**
 * Get the CSS color class for a risk/severity level.
 */
export function severityColor(level: string): string {
  switch (level) {
    case "critical": return "text-destructive";
    case "high": return "text-orange-400";
    case "medium": return "text-warning";
    case "low": return "text-muted-foreground";
    default: return "text-muted-foreground";
  }
}

/**
 * Get the CSS background class for a risk badge.
 */
export function severityBgColor(level: string): string {
  switch (level) {
    case "critical": return "bg-destructive/10 text-destructive";
    case "high": return "bg-orange-400/10 text-orange-400";
    case "medium": return "bg-warning/10 text-warning";
    case "low": return "bg-muted text-muted-foreground";
    default: return "bg-muted text-muted-foreground";
  }
}
