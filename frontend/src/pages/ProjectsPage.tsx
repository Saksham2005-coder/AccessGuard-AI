import { FolderKanban, Plus } from "lucide-react";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";

export function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Projects</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your monitored web domains and DNS verification status.
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      <EmptyState
        icon={FolderKanban}
        title="No projects configured"
        description="Create your first project to verify domain ownership and initiate automated accessibility scanning."
        action={
          <Button>
            <Plus className="h-4 w-4" />
            <span>Create Project</span>
          </Button>
        }
      />
    </div>
  );
}
