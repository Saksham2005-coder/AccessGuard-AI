import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { listProjectsApi } from "../api/projects";
import {
  getFindingApi,
  listFindingsApi,
} from "../api/findings";
import { FindingDetailDrawer } from "../components/findings/FindingDetailDrawer";

export function FindingsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedImpact, setSelectedImpact] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Fetch projects for filtering
  const { data: projectsData } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const projects = projectsData?.items || [];

  // Fetch findings
  const {
    data: findingsData,
    isLoading: findingsLoading,
    isError,
  } = useQuery({
    queryKey: ["findings", selectedProjectId, selectedImpact],
    queryFn: () =>
      listFindingsApi({
        project_id: selectedProjectId || undefined,
        impact: selectedImpact || undefined,
      }),
  });

  // Fetch finding details when opened
  const { data: selectedFinding } = useQuery({
    queryKey: ["finding", selectedFindingId],
    queryFn: () => (selectedFindingId ? getFindingApi(selectedFindingId) : null),
    enabled: Boolean(selectedFindingId),
  });

  const handleOpenDetail = (findingId: string) => {
    setSelectedFindingId(findingId);
    setIsDetailOpen(true);
  };

  // Client-side text filter by rule ID or selector
  const findings = useMemo(() => {
    const rawFindings = findingsData?.items || [];
    if (!searchQuery.trim()) return rawFindings;
    const q = searchQuery.toLowerCase();
    return rawFindings.filter(
      (f) =>
        f.axe_rule_id.toLowerCase().includes(q) ||
        f.description.toLowerCase().includes(q) ||
        (f.selector && f.selector.toLowerCase().includes(q))
    );
  }, [findingsData?.items, searchQuery]);

  const getImpactBadgeVariant = (impact?: string | null) => {
    switch (impact) {
      case "critical":
        return "critical";
      case "serious":
        return "serious";
      case "moderate":
        return "moderate";
      case "minor":
        return "minor";
      default:
        return "default";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
          Findings Explorer
        </h1>
        <p className="text-sm text-[#9CA3AF] mt-1">
          Detailed accessibility barrier telemetry, DOM nodes, WCAG criterion mapping, and AI remediation routing.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-[#171A1F]">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
            <input
              type="text"
              placeholder="Search rule ID or selector (e.g. image-alt, .btn)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-full rounded-lg border border-[#303741] bg-[#171C23] pl-9 pr-3 text-xs text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors font-mono"
            />
          </div>

          <div className="flex items-center gap-2.5">
            {/* Impact Filter */}
            <div className="relative">
              <select
                value={selectedImpact}
                onChange={(e) => setSelectedImpact(e.target.value)}
                className="h-9 rounded-lg border border-[#303741] bg-[#171C23] px-3 text-xs font-medium text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors cursor-pointer"
                aria-label="Filter findings by impact severity"
              >
                <option value="" className="bg-[#1D2229]">All Severities</option>
                <option value="critical" className="bg-[#1D2229]">Critical</option>
                <option value="serious" className="bg-[#1D2229]">Serious</option>
                <option value="moderate" className="bg-[#1D2229]">Moderate</option>
                <option value="minor" className="bg-[#1D2229]">Minor</option>
              </select>
            </div>

            {/* Project Filter */}
            {projects.length > 0 && (
              <div className="relative">
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="h-9 rounded-lg border border-[#303741] bg-[#171C23] px-3 text-xs font-medium text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors cursor-pointer"
                  aria-label="Filter findings by project"
                >
                  <option value="" className="bg-[#1D2229]">All Projects</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id} className="bg-[#1D2229]">
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Loading Skeletons */}
      {findingsLoading && (
        <Card className="p-6 space-y-4">
          <Skeleton className="h-6 w-1/4" />
          <div className="space-y-3 pt-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!findingsLoading && !isError && findings.length === 0 && (
        <EmptyState
          icon={ShieldAlert}
          title="No Accessibility Findings Match Query"
          description="Either all audited pages are barrier-free for the selected filter, or no scans have been performed yet."
        />
      )}

      {/* Findings Table */}
      {!findingsLoading && !isError && findings.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#171A1F] border-b border-[#303741] text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5 font-semibold">Severity</th>
                  <th className="px-5 py-3.5 font-semibold">axe Rule ID</th>
                  <th className="px-5 py-3.5 font-semibold">Issue Description</th>
                  <th className="px-5 py-3.5 font-semibold">DOM Selector</th>
                  <th className="px-5 py-3.5 font-semibold">WCAG Criteria</th>
                  <th className="px-5 py-3.5 text-right font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#303741] bg-[#1D2229]">
                {findings.map((finding) => (
                  <tr
                    key={finding.id}
                    className="hover:bg-[#252C35]/60 transition-colors group cursor-pointer"
                    onClick={() => handleOpenDetail(finding.id)}
                  >
                    <td className="px-5 py-4">
                      <Badge
                        variant={getImpactBadgeVariant(finding.impact)}
                        className="capitalize text-xs font-semibold"
                      >
                        {finding.impact || "unspecified"}
                      </Badge>
                    </td>

                    <td className="px-5 py-4 font-mono font-bold text-xs text-[#38BDF8]">
                      {finding.axe_rule_id}
                    </td>

                    <td className="px-5 py-4 text-xs text-[#F3F4F6] max-w-md">
                      <div className="font-medium line-clamp-1">{finding.description}</div>
                      {finding.help && (
                        <div className="text-[11px] text-[#9CA3AF] line-clamp-1 mt-0.5">
                          {finding.help}
                        </div>
                      )}
                    </td>

                    <td className="px-5 py-4 font-mono text-xs text-[#9CA3AF] max-w-xs truncate">
                      <span className="bg-[#171C23] border border-[#303741] px-2 py-0.5 rounded text-[11px] text-[#38BDF8]">
                        {finding.selector || "document"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(finding.wcag_tags || []).slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="inline-block px-1.5 py-0.5 rounded bg-[#171C23] border border-[#303741] text-[10px] font-mono text-[#9CA3AF]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>

                    <td className="px-5 py-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetail(finding.id);
                        }}
                        className="text-xs gap-1.5"
                      >
                        <Sparkles className="h-3.5 w-3.5 text-[#38BDF8]" />
                        <span>Inspect</span>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Finding Detail Drawer */}
      <FindingDetailDrawer
        finding={selectedFinding || null}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedFindingId(null);
        }}
      />
    </div>
  );
}
