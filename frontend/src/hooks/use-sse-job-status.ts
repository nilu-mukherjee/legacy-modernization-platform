"use client";

import { useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SSEJobState {
  progress: number;
  currentStep: string;
  status: "pending" | "running" | "completed" | "failed";
  isComplete: boolean;
  isFailed: boolean;
  error: string | null;
}

/**
 * Stream job progress via Server-Sent Events instead of polling.
 * Uses fetch + ReadableStream so the Authorization header can be sent.
 */
export function useSSEJobStatus(
  jobId: string | null,
  authToken: string | null,
): SSEJobState {
  const [state, setState] = useState<SSEJobState>({
    progress: 0,
    currentStep: "Initializing…",
    status: "pending",
    isComplete: false,
    isFailed: false,
    error: null,
  });

  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!jobId || !authToken) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    (async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/jobs/${jobId}/stream`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
            signal: controller.signal,
          },
        );

        if (!res.ok || !res.body) {
          setState((s) => ({ ...s, error: `Stream error ${res.status}` }));
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n\n");
          buf = lines.pop() ?? "";

          for (const chunk of lines) {
            const dataLine = chunk
              .split("\n")
              .find((l) => l.startsWith("data:"));
            if (!dataLine) continue;

            try {
              const event = JSON.parse(dataLine.slice(5).trim()) as {
                progress: number;
                current_step: string;
                status: string;
              };

              const isComplete = event.status === "completed";
              const isFailed = event.status === "failed";

              setState({
                progress: event.progress,
                currentStep: event.current_step,
                status: event.status as SSEJobState["status"],
                isComplete,
                isFailed,
                error: null,
              });

              if (isComplete || isFailed) {
                reader.cancel();
                return;
              }
            } catch {
              // malformed event — skip
            }
          }
        }
      } catch (err: unknown) {
        if ((err as { name?: string })?.name === "AbortError") return;
        setState((s) => ({
          ...s,
          error: err instanceof Error ? err.message : "Stream failed",
        }));
      }
    })();

    return () => controller.abort();
  }, [jobId, authToken]);

  return state;
}
