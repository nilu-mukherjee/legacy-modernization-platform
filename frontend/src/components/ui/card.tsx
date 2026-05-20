/**
 * @fileoverview Card component suite for surface containers.
 *
 * Provides `Card`, `CardHeader`, `CardTitle`, `CardDescription`,
 * `CardContent`, and `CardFooter` — composable building blocks for
 * any card-style layout.
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardHeader>
 *     <CardTitle>Project Alpha</CardTitle>
 *     <CardDescription>Last analysed 2 hours ago</CardDescription>
 *   </CardHeader>
 *   <CardContent>…</CardContent>
 *   <CardFooter>…</CardFooter>
 * </Card>
 * ```
 */

import * as React from "react";
import { cn } from "@/lib/utils";

/* ── Card ──────────────────────────────────────────────────────────────── */

/**
 * Root card container.
 *
 * Uses a dark, semi-transparent background with a subtle border
 * and shadow for the glassmorphism aesthetic.
 */
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border border-border bg-card text-card-foreground shadow-lg shadow-black/5 transition-all duration-200",
      className,
    )}
    {...props}
  />
));
Card.displayName = "Card";

/* ── CardHeader ────────────────────────────────────────────────────────── */

/** Header section with standard padding and spacing. */
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

/* ── CardTitle ─────────────────────────────────────────────────────────── */

/** Card title — renders as an `<h3>` by default. */
const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className,
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

/* ── CardDescription ───────────────────────────────────────────────────── */

/** Muted description text below the title. */
const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

/* ── CardContent ───────────────────────────────────────────────────────── */

/** Main content area with horizontal/bottom padding. */
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

/* ── CardFooter ────────────────────────────────────────────────────────── */

/** Footer section — typically used for action buttons. */
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
};
