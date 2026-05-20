/**
 * @fileoverview Skeleton loading placeholder component.
 *
 * Renders a pulsing rectangular placeholder that indicates content
 * is loading.  Uses the custom `pulse-slow` animation from globals.css.
 *
 * @example
 * ```tsx
 * <Skeleton className="h-4 w-[250px]" />
 * <Skeleton className="h-12 w-full rounded-xl" />
 * ```
 */

import { cn } from "@/lib/utils";

/**
 * Animated skeleton placeholder.
 *
 * Apply `className` to control dimensions (`h-*`, `w-*`) and shape
 * (`rounded-*`).  The background pulses between two shades of the
 * muted colour token.
 *
 * @param className - Tailwind classes for sizing and shape
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse-slow rounded-lg bg-muted/50",
        className,
      )}
      {...props}
    />
  );
}

export { Skeleton };
