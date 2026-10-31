import { FileText } from "lucide-react";
import { EmptyState } from "../components/ui/EmptyState";

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Export structured JSON datasets and shareable accessibility audit reports.
          </p>
        </div>
      </div>

      <EmptyState
        icon={FileText}
        title="No reports generated"
        description="Audit reports can be generated and exported upon completing website accessibility scans."
      />
    </div>
  );
}
