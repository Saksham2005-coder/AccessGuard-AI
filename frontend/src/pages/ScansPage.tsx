import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ExternalLink,
  History,
  Play,
  RotateCw,
  ShieldAlert,
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
import { RegressionMonitoringModal } from "../components/regression/RegressionMonitoringModal";

export function ScansPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [regressionScan, setRegressionScan] = useState<Scan | null>(null);
  const [isRegressionOpen, setIsRegressionOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  // Fetch available projects
  const { data: projectsData } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const projects = projectsData?.items || [];
  const activeProjectId = selectedProjectId || projects[0]?.id || "";
  const activeProject = projects.find((p) => p.id === activeProjectId);

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
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            Accessibility Scans
          </h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Real-time multi-page crawling, axe-core 4.14.0 audits, and scan execution telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {projects.length > 0 && (
            <div className="relative">
              <select
                value={activeProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="h-9 rounded-lg border border-[#303741] bg-[#171C23] px-3 py-1.5 text-xs font-medium text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors cursor-pointer"
                aria-label="Filter scans by project"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id} className="bg-[#1D2229] text-[#F3F4F6]">
                    {p.name} ({p.base_domain})
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button
            onClick={() => setIsCreateOpen(true)}
            disabled={projects.length === 0}
            className="gap-2 shrink-0 font-semibold"
          >
            <Play className="h-4 w-4 fill-current" />
            <span>New Scan</span>
          </Button>
        </div>
      </div>

      {/* Domain Verification Notice if Active Project is Unverified */}
      {activeProject && !activeProject.is_verified && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-[#FBBF24] shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-semibold text-[#FBBF24] uppercase tracking-wider">
                Domain Verification Required
              </span>
              <p className="text-[#9CA3AF] mt-0.5">
                Target domain <code className="text-[#F3F4F6] font-mono">{activeProject.base_domain}</code> has not proven DNS ownership yet. Please configure the DNS TXT challenge in Projects before launching audit scans.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeletons */}
      {scansLoading && (
        <Card className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/4" />
          <div className="space-y-3 pt-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </Card>
      )}

      {/* Error Banner */}
      {scansError && (
        <Card className="border-rose-500/30 bg-rose-500/10 p-6 text-center">
          <div className="flex flex-col items-center gap-2">
            <ShieldAlert className="h-8 w-8 text-[#FB7185]" />
            <p className="text-sm text-[#FB7185] font-semibold">
              Failed to load scan records for this project.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2 text-xs">
              <RotateCw className="h-3.5 w-3.5 mr-1" />
              <span>Retry</span>
            </Button>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!scansLoading && !scansError && scans.length === 0 && (
        <EmptyState
          icon={Activity}
          title="No Scans Executed for this Project"
          description="Initiate an automated scan to crawl pages, inject axe-core, and report WCAG violations with isolated snapshot validation."
          action={
            <Button
              onClick={() => setIsCreateOpen(true)}
              disabled={!activeProject?.is_verified}
              className="gap-2"
            >
              <Play className="h-4 w-4 fill-current" />
              <span>Initiate First Scan</span>
            </Button>
          }
        />
      )}

      {/* Scans Table */}
      {!scansLoading && !scansError && scans.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#171A1F] border-b border-[#303741] text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5 font-semibold">Target URL</th>
                  <th className="px-5 py-3.5 font-semibold">Status</th>
                  <th className="px-5 py-3.5 font-semibold">Pages Crawled</th>
                  <th className="px-5 py-3.5 font-semibold">Violations</th>
                  <th className="px-5 py-3.5 font-semibold">Engine</th>
                  <th className="px-5 py-3.5 font-semibold">Executed At</th>
                  <th className="px-5 py-3.5 text-right font-semibold">Telemetry</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#303741] bg-[#1D2229]">
                {scans.map((scan) => {
                  const isActive = ["pending", "running", "crawling", "auditing"].includes(
                    scan.status
                  );
                  const isCompleted =
                    scan.status === "completed" || scan.status === "completed_with_errors";
                  const isFailed = scan.status === "failed" || scan.status === "cancelled";

                  const badgeVariant = isCompleted
                    ? "success"
                    : isFailed
                    ? "critical"
                    : "primary";

                  return (
                    <tr
                      key={scan.id}
                      className="hover:bg-[#252C35]/60 transition-colors group cursor-pointer"
                      onClick={() => handleOpenDetail(scan.id)}
                    >
                      <td className="px-5 py-4 font-mono text-xs text-[#F3F4F6] font-medium max-w-sm truncate">
                        <div className="flex items-center gap-2">
                          <span className="truncate">{scan.target_url}</span>
                          <ExternalLink className="h-3 w-3 text-[#6B7280] opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <Badge
                          variant={badgeVariant}
                          className="capitalize text-xs gap-1.5"
                        >
                          {isActive && (
                            <span className="relative flex h-1.5 w-1.5">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#38BDF8] opacity-75" />
                              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#38BDF8]" />
                            </span>
                          )}
                          <span>{scan.status}</span>
                        </Badge>
                      </td>

                      <td className="px-5 py-4 text-xs font-mono text-[#9CA3AF]">
                        <span className="text-[#F3F4F6] font-semibold">{scan.pages_succeeded}</span>
                        <span> / </span>
                        <span>{scan.total_pages || scan.config?.max_pages || 1}</span>
                      </td>

                      <td className="px-5 py-4 font-mono font-bold text-xs">
                        <span className={scan.total_violations > 0 ? "text-[#FB7185]" : "text-[#34D399]"}>
                          {scan.total_violations}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-xs text-[#9CA3AF]">
                        axe-core {scan.axe_version || "4.14.0"}
                      </td>

                      <td className="px-5 py-4 text-xs text-[#9CA3AF]">
                        {new Date(scan.created_at).toLocaleString()}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDetail(scan.id);
                            }}
                            className="text-xs gap-1.5"
                          >
                            <Activity className="h-3.5 w-3.5 text-[#38BDF8]" />
                            <span>View Telemetry</span>
                          </Button>
                          {isCompleted && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                setRegressionScan(scan);
                                setIsRegressionOpen(true);
                              }}
                              className="text-xs gap-1.5 text-indigo-400 border-indigo-900/40 hover:bg-indigo-950/20"
                            >
                              <History className="h-3.5 w-3.5 text-indigo-400" />
                              <span>Regressions</span>
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Create Scan Modal */}
      <CreateScanModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        projects={projects}
        preselectedProjectId={activeProjectId}
        onScanCreated={handleScanCreated}
      />

      {/* Scan Detail & Telemetry Modal */}
      <ScanDetailModal
        scanId={selectedScanId}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedScanId(null);
        }}
        onScanUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ["scans", activeProjectId] });
        }}
        onInspectFinding={(findingId) => {
          navigate(`/app/findings?finding_id=${findingId}`);
        }}
      />

      {/* Regression Monitoring Modal */}
      {regressionScan && (
        <RegressionMonitoringModal
          isOpen={isRegressionOpen}
          onClose={() => {
            setIsRegressionOpen(false);
            setRegressionScan(null);
          }}
          projectId={activeProjectId}
          currentScan={regressionScan}
          availableScans={scans}
        />
      )}
    </div>
  );
}
