import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Play,
  RotateCw,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { listProjectsApi } from "../api/projects";
import { listProjectScansApi, Scan } from "../api/scans";
import { CreateScanModal } from "../components/scans/CreateScanModal";
import { ScanDetailModal } from "../components/scans/ScanDetailModal";

export function ScansPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  // Fetch available projects
  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const projects = projectsData?.items || [];
  const activeProjectId = selectedProjectId || projects[0]?.id || "";

  // Fetch scans for the active project
  const {
    data: scansData,
    isLoading: scansLoading,
    isError: scansError,
    refetch,
  } = useQuery({
    queryKey: ["scans", activeProjectId],
    queryFn: () => listProjectScansApi(activeProjectId),
    enabled: Boolean(activeProjectId),
    refetchInterval: (query) => {
      const scans = query.state.data?.items || [];
      const hasActive = scans.some((s) =>
        ["pending", "running", "crawling", "auditing"].includes(s.status)
      );
      return hasActive ? 3000 : false;
    },
  });

  const scans = scansData?.items || [];

  const handleOpenDetail = (scanId: string) => {
    setSelectedScanId(scanId);
    setIsDetailOpen(true);
  };

  const handleScanCreated = (newScan: Scan) => {
    queryClient.invalidateQueries({ queryKey: ["scans", activeProjectId] });
    handleOpenDetail(newScan.id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Accessibility Scans
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time multi-page crawling, axe-core 4.14.0 audits, and scan execution telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {projects.length > 0 && (
            <select
              value={activeProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20"
              aria-label="Filter scans by project"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}

          <Button
            onClick={() => setIsCreateOpen(true)}
            disabled={projects.length === 0}
            className="gap-2 shrink-0"
          >
            <Play className="h-4 w-4" />
            <span>Start Scan</span>
          </Button>
        </div>
      </div>

      {/* Loading Skeletons */}
      {(scansLoading || projectsLoading) && (
        <Card className="p-6 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <div className="space-y-2 w-1/3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-8 w-24" />
            </div>
          ))}
        </Card>
      )}

      {/* Error Banner */}
      {scansError && (
        <Card className="border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-800 font-medium mb-3">
            Failed to load project scans. Please check your connection.
          </p>
          <Button variant="outline" onClick={() => refetch()} className="mx-auto text-xs gap-1.5">
            <RotateCw className="h-3.5 w-3.5" />
            Retry
          </Button>
        </Card>
      )}

      {/* Empty State when no projects exist */}
      {!projectsLoading && projects.length === 0 && (
        <EmptyState
          icon={Activity}
          title="No projects configured"
          description="Create and verify a project before initiating automated accessibility scans."
        />
      )}

      {/* Empty State when project has no scans */}
      {!scansLoading && !scansError && projects.length > 0 && scans.length === 0 && (
        <EmptyState
          icon={Activity}
          title="No scans executed yet"
          description="Start your first automated scan to crawl verified pages and detect accessibility violations."
          action={
            <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
              <Play className="h-4 w-4" />
              <span>Start First Scan</span>
            </Button>
          }
        />
      )}

      {/* Scans Table */}
      {!scansLoading && !scansError && scans.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-5 py-3">Target Endpoint</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3">Pages Audited</th>
                  <th scope="col" className="px-4 py-3">Violations</th>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scans.map((scan) => {
                  const isActive = [
                    "pending",
                    "running",
                    "crawling",
                    "auditing",
                  ].includes(scan.status);
                  const isCompleted = [
                    "completed",
                    "completed_with_errors",
                  ].includes(scan.status);

                  return (
                    <tr key={scan.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-1.5 font-mono text-xs font-medium text-slate-900 max-w-xs truncate">
                          <span className="truncate">{scan.target_url}</span>
                          <a
                            href={scan.target_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-400 hover:text-slate-600"
                            aria-label={`Open target url ${scan.target_url}`}
                          >
                            <ExternalLink className="h-3 w-3 shrink-0" />
                          </a>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge
                          variant={
                            isActive
                              ? "default"
                              : isCompleted
                                ? "success"
                                : "critical"
                          }
                          className="capitalize text-xs gap-1"
                        >
                          {isActive && <Activity className="h-3 w-3 animate-spin" />}
                          {isCompleted && <CheckCircle2 className="h-3 w-3" />}
                          {!isActive && !isCompleted && <AlertCircle className="h-3 w-3" />}
                          <span>{scan.status.replace("_", " ")}</span>
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5 text-xs text-slate-700">
                        <span className="font-semibold text-slate-900">
                          {scan.pages_succeeded + scan.pages_failed}
                        </span>
                        <span className="text-slate-400">
                          /{scan.config?.max_pages ? Number(scan.config.max_pages) : 20}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        {scan.total_violations > 0 ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                            {scan.total_violations}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            0
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-xs text-slate-500 whitespace-nowrap">
                        {new Date(scan.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td className="px-5 py-3.5 text-right whitespace-nowrap">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenDetail(scan.id)}
                          className="text-xs"
                        >
                          View Telemetry
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Creation Modal */}
      <CreateScanModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        projects={projects}
        preselectedProjectId={activeProjectId}
        onScanCreated={handleScanCreated}
      />

      {/* Detail / Progress Modal */}
      <ScanDetailModal
        scanId={selectedScanId}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onScanUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ["scans", activeProjectId] });
        }}
      />
    </div>
  );
}
