import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#38BDF8] focus-visible:ring-offset-2 focus-visible:ring-offset-[#111315] disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-[#38BDF8] text-[#111315] font-semibold hover:bg-[#0EA5E9] shadow-sm shadow-[#38BDF8]/10 active:scale-[0.98]",
        secondary:
          "bg-[#252C35] text-[#F3F4F6] hover:bg-[#303741] border border-[#303741] hover:border-[#38BDF8]/30",
        outline:
          "border border-[#303741] bg-[#171C23]/60 text-[#F3F4F6] hover:bg-[#1D2229] hover:border-[#38BDF8]/40 hover:text-[#38BDF8]",
        ghost:
          "text-[#9CA3AF] hover:bg-[#252C35] hover:text-[#F3F4F6]",
        destructive:
          "bg-rose-500/15 text-[#FB7185] hover:bg-rose-500/25 border border-rose-500/30 focus-visible:ring-rose-500",
        link:
          "text-[#38BDF8] underline-offset-4 hover:underline p-0 h-auto hover:text-[#0EA5E9]",
        success:
          "bg-emerald-500/15 text-[#34D399] hover:bg-emerald-500/25 border border-emerald-500/30",
      },
      size: {
        sm: "h-8 px-3 text-xs rounded-md",
        md: "h-9 px-4 py-2",
        lg: "h-10 px-5 text-base rounded-lg",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        disabled={disabled || isLoading}
        aria-busy={isLoading ? "true" : undefined}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
