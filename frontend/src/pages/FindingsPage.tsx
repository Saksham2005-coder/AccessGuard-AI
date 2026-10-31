import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Code,
  ExternalLink,
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
  Finding,
  FindingDetail,
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
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Findings Explorer
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Explore automated axe-core accessibility violations, inspect selectors, and initiate AI remediation.
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-200 bg-white shadow-2xs">
        <div className="flex flex-1 items-center gap-2.5">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search rule ID or selector..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
          </div>

          {/* Project Filter */}
          {projects.length > 0 && (
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-[#4657D8] focus:bg-white focus:outline-none"
              aria-label="Filter by project"
            >
              <option value="">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}

          {/* Severity Impact Filter */}
          <select
            value={selectedImpact}
            onChange={(e) => setSelectedImpact(e.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-[#4657D8] focus:bg-white focus:outline-none"
            aria-label="Filter by impact severity"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="serious">Serious</option>
            <option value="moderate">Moderate</option>
            <option value="minor">Minor</option>
          </select>
        </div>

        <div className="text-xs text-slate-400 font-medium px-1">
          {findings.length} {findings.length === 1 ? "violation" : "violations"}
        </div>
      </div>

      {/* Loading Skeleton */}
      {findingsLoading && (
        <Card className="p-6 space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <div className="space-y-2 w-1/3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-8 w-28" />
            </div>
          ))}
        </Card>
      )}

      {/* Error Banner */}
      {isError && (
        <Card className="border-red-200 bg-red-50 p-6 text-center text-red-800 text-sm">
          Failed to load accessibility findings. Please ensure your session is active.
        </Card>
      )}

      {/* Empty State */}
      {!findingsLoading && !isError && findings.length === 0 && (
        <EmptyState
          icon={ShieldAlert}
          title={searchQuery || selectedImpact || selectedProjectId ? "No matching findings" : "No findings detected"}
          description={
            searchQuery || selectedImpact || selectedProjectId
              ? "No accessibility violations match your selected filters. Try broadening your criteria."
              : "Launch an automated website scan to crawl pages and detect WCAG violations."
          }
        />
      )}

      {/* Findings Table */}
      {!findingsLoading && !isError && findings.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-5 py-3">Rule ID & Description</th>
                  <th scope="col" className="px-4 py-3">Impact</th>
                  <th scope="col" className="px-4 py-3">Target Element</th>
                  <th scope="col" className="px-4 py-3">WCAG Criteria</th>
                  <th scope="col" className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {findings.map((f: Finding) => (
                  <tr key={f.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5 max-w-sm">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-900 font-mono text-xs flex items-center gap-1.5">
                          <span>{f.axe_rule_id}</span>
                          {f.help_url && (
                            <a
                              href={f.help_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-400 hover:text-slate-600"
                              aria-label={`Rule guidance for ${f.axe_rule_id}`}
                            >
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-1">{f.description}</p>
                      </div>
                    </td>

                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <Badge
                        variant={getImpactBadgeVariant(f.impact)}
                        className="capitalize text-xs font-semibold"
                      >
                        {f.impact || "unspecified"}
                      </Badge>
                    </td>

                    <td className="px-4 py-3.5 max-w-xs">
                      {f.selector ? (
                        <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-700 bg-slate-100 px-2 py-1 rounded-md max-w-full truncate">
                          <Code className="h-3 w-3 shrink-0 text-slate-400" />
                          <span className="truncate">{f.selector}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">No selector</span>
                      )}
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {f.wcag_tags?.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200"
                          >
                            {tag}
                          </span>
                        ))}
                        {f.wcag_tags?.length > 3 && (
                          <span className="text-[10px] text-slate-400">
                            +{f.wcag_tags.length - 3}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenDetail(f.id)}
                        className="gap-1.5 text-xs"
                      >
                        <Sparkles className="h-3.5 w-3.5 text-[#4657D8]" />
                        <span>Inspect</span>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Finding Detail Inspection Drawer */}
      <FindingDetailDrawer
        finding={(selectedFinding as FindingDetail) || null}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />
    </div>
  );
}
