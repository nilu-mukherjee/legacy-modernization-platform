/**
 * Score Gauge Component
 * =====================
 * Animated circular gauge that displays the modernization readiness
 * score with a grade letter in the center. The ring fills with a
 * gradient based on the score value.
 */

"use client";

import { useEffect, useState } from "react";
import { cn, gradeColor } from "@/lib/utils";

interface ScoreGaugeProps {
  /** Score from 0 to 100. */
  score: number;
  /** Letter grade (A-F). */
  grade: string;
  /** Diameter of the gauge in pixels. */
  size?: number;
  /** Optional CSS class. */
  className?: string;
}

/**
 * Map a 0-100 score to an SVG stroke color.
 */
function scoreStrokeColor(score: number): string {
  if (score >= 80) return "#22c55e"; // green-500
  if (score >= 60) return "#84cc16"; // lime-500
  if (score >= 40) return "#eab308"; // yellow-500
  if (score >= 20) return "#f97316"; // orange-500
  return "#ef4444"; // red-500
}

export default function ScoreGauge({
  score,
  grade,
  size = 180,
  className,
}: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Animate the score counter on mount.
  useEffect(() => {
    const duration = 1500; // ms
    const steps = 60;
    const increment = score / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setAnimatedScore(score);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [score]);

  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedScore / 100) * circumference;
  const strokeColor = scoreStrokeColor(score);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className="-rotate-90"
      >
        {/* Background ring */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          className="text-muted/30"
        />
        {/* Score ring */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          style={{
            filter: `drop-shadow(0 0 6px ${strokeColor}40)`,
          }}
        />
      </svg>

      {/* Center text */}
      <div className="absolute flex flex-col items-center">
        <span className={cn("text-4xl font-extrabold", gradeColor(grade))}>
          {animatedScore}%
        </span>
        <span className="text-xs font-medium text-muted-foreground">
          Grade {grade}
        </span>
      </div>
    </div>
  );
}
