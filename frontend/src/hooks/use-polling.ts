/**
 * @fileoverview Generic polling hook for CodeLens AI.
 *
 * `usePolling` repeatedly calls an async fetcher at a configurable interval
 * and stops when a user-defined condition is met or the component unmounts.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = usePolling(
 *   () => api.getJobStatus(jobId),
 *   3000,
 *   (job) => job.status === "completed" || job.status === "failed",
 * );
 * ```
 */

"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/** Options for the usePolling hook. */
interface UsePollingOptions<T> {
  /** Whether polling is enabled (default: true). */
  enabled?: boolean;
  /** Callback invoked when the stop condition is met. */
  onComplete?: (data: T) => void;
  /** Callback invoked when an error occurs during polling. */
  onError?: (error: Error) => void;
}

/** Return value of the usePolling hook. */
interface UsePollingResult<T> {
  /** Latest data returned by the fetcher. */
  data: T | null;
  /** Whether the initial fetch is in progress. */
  isLoading: boolean;
  /** Last error encountered (null if none). */
  error: Error | null;
  /** Whether polling has stopped (condition met or error). */
  isComplete: boolean;
  /** Manually restart polling. */
  restart: () => void;
}

/**
 * Poll an async function at a fixed interval until a stop condition is met.
 *
 * @param fetcher      - Async function that returns data of type `T`
 * @param intervalMs   - Polling interval in milliseconds
 * @param stopCondition - Predicate that returns `true` to stop polling
 * @param options      - Additional options (enabled, callbacks)
 * @returns Polling state and controls
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  stopCondition: (data: T) => boolean,
  options: UsePollingOptions<T> = {},
): UsePollingResult<T> {
  const { enabled = true, onComplete, onError } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  /** Execute a single poll cycle. */
  const poll = useCallback(async () => {
    try {
      const result = await fetcher();
      if (!mountedRef.current) return;

      setData(result);
      setIsLoading(false);
      setError(null);

      if (stopCondition(result)) {
        setIsComplete(true);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        onComplete?.(result);
      }
    } catch (err) {
      if (!mountedRef.current) return;
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      setIsLoading(false);
      onError?.(e);
    }
  }, [fetcher, stopCondition, onComplete, onError]);

  /** Start or restart polling. */
  const restart = useCallback(() => {
    setIsComplete(false);
    setError(null);
    setIsLoading(true);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Immediate first call
    poll();

    intervalRef.current = setInterval(poll, intervalMs);
  }, [poll, intervalMs]);

  useEffect(() => {
    mountedRef.current = true;

    if (enabled && !isComplete) {
      poll();
      intervalRef.current = setInterval(poll, intervalMs);
    }

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  return { data, isLoading, error, isComplete, restart };
}
