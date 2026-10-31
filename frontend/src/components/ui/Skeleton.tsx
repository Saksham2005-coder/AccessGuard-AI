import React from "react";
import { cn } from "../../lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-[#252C35]/80", className)}
      aria-hidden="true"
      {...props}
    />
  );
}
