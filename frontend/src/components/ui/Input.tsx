import React from "react";
import { cn } from "../../lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", label, error, helperText, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
    const errorId = inputId ? `${inputId}-error` : undefined;
    const helperId = inputId ? `${inputId}-helper` : undefined;

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider select-none"
          >
            {label}
            {props.required && <span className="text-[#FB7185] ml-1" aria-hidden="true">*</span>}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          className={cn(
            "flex h-9 w-full rounded-lg border border-[#303741] bg-[#171C23] px-3 py-1.5 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs transition-colors",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#F3F4F6]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#38BDF8] focus-visible:border-transparent",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#111315]",
            error && "border-[#FB7185] focus-visible:ring-[#FB7185]",
            className
          )}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={
            [error ? errorId : null, helperText ? helperId : null]
              .filter(Boolean)
              .join(" ") || undefined
          }
          {...props}
        />
        {helperText && !error && (
          <p id={helperId} className="text-xs text-[#9CA3AF]">
            {helperText}
          </p>
        )}
        {error && (
          <p id={errorId} className="text-xs text-[#FB7185] font-medium" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
