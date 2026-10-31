import { Sparkles } from "lucide-react";
import { EmptyState } from "../components/ui/EmptyState";

export function RemediationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">AI Remediation Review</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review evidence-grounded code proposals, approve safe patches, and verify snapshot tests.
        </p>
      </div>

      <EmptyState
        icon={Sparkles}
        title="No remediation proposals pending"
        description="Select an accessibility finding to trigger grounded LangGraph analysis and code patch proposal."
      />
    </div>
  );
}
