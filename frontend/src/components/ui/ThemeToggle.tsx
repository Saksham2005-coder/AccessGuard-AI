import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, resolvedTheme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center justify-center p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] border border-[var(--border-graphite)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)] ${className}`}
      aria-label={`Current theme is ${theme}. Click to switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode.`}
      title={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
    >
      {resolvedTheme === "dark" ? (
        <Sun className="h-4 w-4 text-amber-400" />
      ) : (
        <Moon className="h-4 w-4 text-blue-500" />
      )}
    </button>
  );
}
