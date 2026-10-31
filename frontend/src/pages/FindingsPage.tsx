import { ShieldAlert } from "lucide-react";
import { EmptyState } from "../components/ui/EmptyState";

export function FindingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Findings Explorer</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse detected violations, impact levels, selectors, and grounded WCAG citations.
          </p>
        </div>
      </div>

      <EmptyState
        icon={ShieldAlert}
        title="No accessibility findings"
        description="Run a website scan to detect automated WCAG violations and reviewable nodes."
      />
    </div>
  );
}
