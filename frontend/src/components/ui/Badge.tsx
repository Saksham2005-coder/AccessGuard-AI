import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default: "bg-[#252C35] text-[#9CA3AF] border border-[#303741]",
        primary: "bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30 font-semibold",
        secondary: "bg-[#252C35] text-[#F3F4F6] border border-[#303741]",
        success: "bg-emerald-500/15 text-[#34D399] border border-emerald-500/30 font-medium",
        warning: "bg-amber-500/15 text-[#FBBF24] border border-amber-500/30 font-medium",
        critical: "bg-rose-500/15 text-[#FB7185] border border-rose-500/30 font-semibold",
        serious: "bg-orange-500/15 text-orange-400 border border-orange-500/30 font-semibold",
        moderate: "bg-amber-500/15 text-[#FBBF24] border border-amber-500/30 font-medium",
        minor: "bg-sky-500/15 text-[#38BDF8] border border-sky-500/30 font-medium",
        outline: "border border-[#303741] text-[#9CA3AF]",
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
