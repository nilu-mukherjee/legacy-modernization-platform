/**
 * @fileoverview Badge component with semantic colour variants.
 *
 * Includes extra `success` and `warning` variants beyond the standard
 * shadcn/ui set to support the CodeLens AI risk-level palette.
 *
 * @example
 * ```tsx
 * <Badge variant="success">Low Risk</Badge>
 * <Badge variant="destructive">Critical</Badge>
 * ```
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Badge style variants.
 *
 * Each variant maps to a specific colour from the design system:
 * - `default`     → Primary indigo
 * - `secondary`   → Muted slate
 * - `destructive` → Rose / red
 * - `outline`     → Transparent with border
 * - `success`     → Emerald / green
 * - `warning`     → Amber / yellow
 */
const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow-sm",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive/15 text-destructive",
        outline: "text-foreground",
        success:
          "border-transparent bg-success/15 text-success",
        warning:
          "border-transparent bg-warning/15 text-warning",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

/** Props accepted by the Badge component. */
export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

/**
 * Inline badge for labels, statuses, and tags.
 *
 * @param props - Badge props including variant
 */
function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };
