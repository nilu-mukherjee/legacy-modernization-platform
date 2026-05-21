/**
 * Sub-Score Radar Chart
 * =====================
 * Displays the 7 modernization dimensions as a radar/spider chart
 * using Recharts.
 */

"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface SubScoreRadarProps {
  /** Sub-scores object from the API. */
  subScores: Record<string, number>;
  /** Optional height in pixels. */
  height?: number;
}

/** Map raw sub-score keys to human-readable short labels. */
const LABELS: Record<string, string> = {
  code_health: "Code",
  dependency_health: "Deps",
  architecture_quality: "Arch",
  test_coverage: "Tests",
  documentation: "Docs",
  infrastructure_readiness: "Infra",
  security_posture: "Security",
};

export default function SubScoreRadar({ subScores, height = 300 }: SubScoreRadarProps) {
  const data = Object.entries(subScores).map(([key, value]) => ({
    dimension: LABELS[key] || key,
    score: value ?? 0,
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="var(--color-border)" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke="oklch(0.541 0.281 275)"
          fill="oklch(0.541 0.281 275)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--color-card)",
            border: "1px solid var(--color-border)",
            borderRadius: "8px",
            color: "var(--color-foreground)",
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
