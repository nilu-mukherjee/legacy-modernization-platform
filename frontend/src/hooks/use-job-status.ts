/**
 * @fileoverview Hook for tracking background job progress in CodeLens AI.
 *
 * Wraps `usePolling` with job-specific defaults and convenience fields
 * like `progress`, `currentStep`, and terminal-state detection.
 *
 * @example
 * ```tsx
 * const { job, progress, isRunning } = useJobStatus(jobId);
 * ```
 */

"use client";

import { useMemo } from "react";
import { usePolling } from "@/hooks/use-polling";
import { api } from "@/lib/api-client";
import { JOB_POLL_INTERVAL_MS } from "@/lib/constants";
import type { Job } from "@/types";

/** Return value of the useJobStatus hook. */
interface UseJobStatusResult {
  /** The latest job object (null until first fetch completes). */
  job: Job | null;
  /** Normalised progress (0–100). */
  progress: number;
  /** Name of the currently-executing step. */
  currentStep: string;
  /** Whether the job is still running. */
  isRunning: boolean;
  /** Whether the job completed successfully. */
  isComplete: boolean;
  /** Whether the job failed. */
  isFailed: boolean;
  /** Whether the initial fetch is in progress. */
  isLoading: boolean;
  /** Error from the last poll cycle, if any. */
  error: Error | null;
  /** Restart polling from scratch. */
  restart: () => void;
}

/**
 * Track a background job's progress with automatic polling.
 *
 * Polls the `/api/v1/jobs/:id` endpoint at `JOB_POLL_INTERVAL_MS` and
 * stops when the job reaches a terminal state (`completed` or `failed`).
 *
 * @param jobId   - Job UUID to track
 * @param enabled - Whether polling should be active (default: true)
 * @returns Job state, progress, and lifecycle flags
 */
export function useJobStatus(
  jobId: string | null,
  enabled = true,
): UseJobStatusResult {
  const fetcher = useMemo(() => {
    if (!jobId) {
      return () =>
        Promise.resolve({
          data: null as unknown as Job,
        });
    }
    return () => api.getJobStatus(jobId);
  }, [jobId]);

  const {
    data: response,
    isLoading,
    error,
    isComplete: pollingStopped,
    restart,
  } = usePolling(
    fetcher,
    JOB_POLL_INTERVAL_MS,
    (res) => {
      const job = res?.data;
      if (!job) return false;
      return job.status === "completed" || job.status === "failed";
    },
    { enabled: enabled && !!jobId },
  );

  const job = response?.data ?? null;

  return {
    job,
    progress: job?.progress ?? 0,
    currentStep: job?.currentStep ?? "Initializing…",
    isRunning: !!job && job.status === "running",
    isComplete: !!job && job.status === "completed",
    isFailed: !!job && job.status === "failed",
    isLoading,
    error,
    restart,
  };
}
