/**
 * @fileoverview Button component built with Class Variance Authority.
 *
 * A polymorphic button supporting multiple visual variants and sizes.
 * Uses `@radix-ui/react-slot` so it can render as a child element
 * (e.g. `<Link>`) when `asChild` is true.
 *
 * @example
 * ```tsx
 * <Button variant="default" size="lg">Get Started</Button>
 * <Button variant="outline" size="sm" asChild>
 *   <Link href="/login">Sign In</Link>
 * </Button>
 * ```
 */

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Button style variants defined with CVA.
 *
 * Base styles include focus-visible ring, disabled opacity, and
 * smooth transitions.  Each variant overrides colours and borders.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 hover:shadow-primary/30",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-border bg-transparent hover:bg-secondary hover:text-secondary-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost:
          "hover:bg-secondary hover:text-secondary-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

/** Props accepted by the Button component. */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * When true, the button renders its child element instead of a `<button>`,
   * merging props. Useful for rendering Next.js `<Link>` as a button.
   */
  asChild?: boolean;
}

/**
 * Primary button component.
 *
 * Supports multiple variants (`default`, `destructive`, `outline`,
 * `secondary`, `ghost`, `link`) and sizes (`default`, `sm`, `lg`, `icon`).
 *
 * @param props - Button props including variant, size, and asChild
 * @param ref   - Forwarded ref to the underlying `<button>` element
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
