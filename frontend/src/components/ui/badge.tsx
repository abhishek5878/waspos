"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        // Pipeline stage badges
        inbound: "border-transparent bg-slate-500/20 text-slate-300",
        screening: "border-transparent bg-blue-500/20 text-blue-300",
        firstMeeting: "border-transparent bg-indigo-500/20 text-indigo-300",
        deepDive: "border-transparent bg-purple-500/20 text-purple-300",
        icReview: "border-transparent bg-amber-500/20 text-amber-300",
        termSheet: "border-transparent bg-emerald-500/20 text-emerald-300",
        closed: "border-transparent bg-green-500/20 text-green-300",
        passed: "border-transparent bg-red-500/20 text-red-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
