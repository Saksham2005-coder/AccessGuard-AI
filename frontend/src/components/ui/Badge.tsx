import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-800 border border-slate-200",
        primary: "bg-[#4657D8]/10 text-[#4657D8] border border-[#4657D8]/20",
        secondary: "bg-slate-100 text-slate-700 border border-slate-200",
        success: "bg-emerald-50 text-emerald-700 border border-emerald-200",
        warning: "bg-amber-50 text-amber-700 border border-amber-200",
        critical: "bg-red-50 text-red-700 border border-red-200",
        serious: "bg-orange-50 text-orange-700 border border-orange-200",
        moderate: "bg-amber-50 text-amber-700 border border-amber-200",
        minor: "bg-sky-50 text-sky-700 border border-sky-200",
        outline: "border border-slate-300 text-slate-700",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
