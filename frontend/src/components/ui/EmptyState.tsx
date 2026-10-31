import React from "react";
import { type LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#303741] bg-[#171A1F]/60 p-12 text-center transition-all",
        className
      )}
    >
      {Icon && (
        <div
          className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#252C35] border border-[#303741] text-[#38BDF8] mb-4 shadow-sm"
          aria-hidden="true"
        >
          <Icon className="h-6 w-6 stroke-[1.75]" />
        </div>
      )}
      <h3 className="text-base font-semibold text-[#F3F4F6]">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-[#9CA3AF] leading-relaxed">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
