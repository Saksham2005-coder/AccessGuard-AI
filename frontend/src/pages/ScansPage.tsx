import { Activity, Play } from "lucide-react";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";

export function ScansPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Accessibility Scans</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time multi-page crawling, axe-core audits, and scan execution history.
          </p>
        </div>
        <Button>
          <Play className="h-4 w-4" />
          <span>Start Scan</span>
        </Button>
      </div>

      <EmptyState
        icon={Activity}
        title="No scans executed yet"
        description="Select a verified domain project to initiate multi-page accessibility auditing."
        action={
          <Button>
            <Play className="h-4 w-4" />
            <span>Launch Audit</span>
          </Button>
        }
      />
    </div>
  );
}
