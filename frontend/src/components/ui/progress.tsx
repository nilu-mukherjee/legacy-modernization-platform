/**
 * @fileoverview Progress bar component using Radix UI primitives.
 *
 * Renders a horizontal progress indicator with a smooth fill animation.
 * The fill colour transitions from indigo to violet (primary gradient).
 *
 * @example
 * ```tsx
 * <Progress value={65} className="h-3" />
 * ```
 */

"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";

import { cn } from "@/lib/utils";

/**
 * Animated horizontal progress bar.
 *
 * @param value     - Current progress (0–100)
 * @param className - Additional CSS classes for the track
 * @param ref       - Forwarded ref
 */
const Progress = React.forwardRef<
  React.ComponentRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-secondary",
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 rounded-full bg-gradient-to-r from-primary to-violet-500 transition-all duration-500 ease-out"
      style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
