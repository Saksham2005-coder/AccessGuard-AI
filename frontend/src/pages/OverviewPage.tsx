import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  FolderKanban,
  Globe,
  Radio,
  Shield,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import { listProjectsApi } from "../api/projects";
import { listProjectScansApi } from "../api/scans";
import { listFindingsApi } from "../api/findings";
import { listRemediationsApi } from "../api/remediations";

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: { name: string; count: number; color: string };
  }>;
}

function DarkChartTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="rounded-lg border border-[#303741] bg-[#1D2229] p-2.5 shadow-xl text-xs text-[#F3F4F6]">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: data.color }} />
          <span className="font-semibold">{data.name}:</span>
          <span className="text-[#38BDF8] font-mono">{data.count}</span>
        </div>
      </div>
    );
  }
  return null;
}

export function OverviewPage() {
  // Query Projects
  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const projects = projectsData?.items || [];
  const activeProject = projects[0];

  // Query Findings
  const { data: findingsData, isLoading: findingsLoading } = useQuery({
    queryKey: ["findings"],
    queryFn: () => listFindingsApi(),
  });

  const findings = findingsData?.items || [];

  // Query Scans for the active project
  const { data: scansData, isLoading: scansLoading } = useQuery({
    queryKey: ["scans", activeProject?.id],
    queryFn: () => (activeProject ? listProjectScansApi(activeProject.id) : null),
    enabled: Boolean(activeProject?.id),
  });

  const scans = scansData?.items || [];

  // Query Remediations
  const { data: remediations = [], isLoading: remediationsLoading } = useQuery({
    queryKey: ["remediations"],
    queryFn: () => listRemediationsApi(),
  });

  // Calculate Metrics
  const verifiedProjectsCount = projects.filter((p) => p.is_verified).length;
  const criticalCount = findings.filter((f) => f.impact === "critical").length;
  const seriousCount = findings.filter((f) => f.impact === "serious").length;
  const moderateCount = findings.filter((f) => f.impact === "moderate").length;
  const minorCount = findings.filter((f) => f.impact === "minor").length;
  const validatedCount = remediations.filter((r) => r.status === "validated").length;

  const totalPagesAudited = scans.reduce((acc, s) => acc + (s.pages_succeeded || 0), 0);

  // Chart Data: Findings Severity Distribution
  const severityData = useMemo(() => [
    { name: "Critical", count: criticalCount, color: "#FB7185" },
    { name: "Serious", count: seriousCount, color: "#FB923C" },
    { name: "Moderate", count: moderateCount, color: "#FBBF24" },
    { name: "Minor", count: minorCount, color: "#38BDF8" },
  ], [criticalCount, seriousCount, moderateCount, minorCount]);

  const isLoading = projectsLoading || findingsLoading || scansLoading;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            Accessibility Overview
          </h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Automated accessibility observability, continuous scan telemetry, and validated AI remediations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/app/scans">
            <Button className="gap-2">
              <Activity className="h-4 w-4" />
              <span>Launch Scan</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Projects Card */}
        <Card className="hover:border-[#38BDF8]/30 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
              Monitored Projects
            </CardTitle>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#252C35] text-[#38BDF8]">
              <FolderKanban className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold text-[#F3F4F6] font-mono">
                  {projects.length}
                </div>
                <div className="flex items-center gap-1.5 mt-1.5 text-xs text-[#9CA3AF]">
                  <Globe className="h-3.5 w-3.5 text-[#34D399]" />
                  <span>{verifiedProjectsCount} verified domains</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Scans Completed Card */}
        <Card className="hover:border-[#38BDF8]/30 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
              Audits Executed
            </CardTitle>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#252C35] text-[#34D399]">
              <Activity className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold text-[#F3F4F6] font-mono">
                  {scans.length}
                </div>
                <div className="flex items-center gap-1.5 mt-1.5 text-xs text-[#9CA3AF]">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#38BDF8]" />
                  <span>{totalPagesAudited} pages crawled</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Critical / Serious Findings Card */}
        <Card className="hover:border-rose-500/30 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
              Open Findings
            </CardTitle>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/15 text-[#FB7185]">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold text-[#F3F4F6] font-mono">
                  {findings.length}
                </div>
                <div className="flex items-center gap-2 mt-1.5 text-xs text-[#9CA3AF]">
                  <span className="text-[#FB7185] font-semibold">{criticalCount} Critical</span>
                  <span>•</span>
                  <span className="text-orange-400 font-semibold">{seriousCount} Serious</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Remediations Validated Card */}
        <Card className="hover:border-[#38BDF8]/30 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
              Snapshot Validated
            </CardTitle>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#38BDF8]/15 text-[#38BDF8]">
              <Sparkles className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            {remediationsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold text-[#F3F4F6] font-mono">
                  {validatedCount}
                </div>
                <div className="flex items-center gap-1.5 mt-1.5 text-xs text-[#9CA3AF]">
                  <Shield className="h-3.5 w-3.5 text-[#34D399]" />
                  <span>Verified in Chromium sandbox</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Two-Column Analytics & Insights Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Severity Distribution Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Findings Severity Distribution</CardTitle>
                <CardDescription>
                  Automated axe-core accessibility violations classified by WCAG impact level.
                </CardDescription>
              </div>
              <Badge variant="outline">axe-core 4.14.0</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {findings.length === 0 ? (
              <div className="h-56 flex flex-col items-center justify-center text-center text-[#9CA3AF]">
                <ShieldAlert className="h-10 w-10 text-[#6B7280] mb-2 stroke-[1.5]" />
                <p className="text-sm font-medium">No accessibility violations detected</p>
                <p className="text-xs text-[#6B7280] mt-1">Audit scans will populate this breakdown</p>
              </div>
            ) : (
              <div className="h-60 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="name"
                      stroke="#6B7280"
                      fontSize={12}
                      tickLine={false}
                      axisLine={{ stroke: "#303741" }}
                    />
                    <YAxis
                      stroke="#6B7280"
                      fontSize={12}
                      tickLine={false}
                      axisLine={{ stroke: "#303741" }}
                      allowDecimals={false}
                    />
                    <Tooltip content={<DarkChartTooltip />} cursor={{ fill: "rgba(56, 189, 248, 0.05)" }} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Engine Architecture & Standards */}
        <Card className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-[#38BDF8]" />
                <CardTitle>Audit Engine Status</CardTitle>
              </div>
              <CardDescription>
                Deterministic multi-stage WCAG evaluation pipeline
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#171C23] border border-[#303741]">
                <span className="text-[#9CA3AF]">Audit Standards</span>
                <span className="font-semibold text-[#F3F4F6]">WCAG 2.1 & 2.2 (A/AA)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#171C23] border border-[#303741]">
                <span className="text-[#9CA3AF]">Core Engine</span>
                <span className="font-semibold text-[#F3F4F6]">axe-core 4.14.0 (Offline)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#171C23] border border-[#303741]">
                <span className="text-[#9CA3AF]">RAG Retriever</span>
                <span className="font-semibold text-[#38BDF8]">Hybrid Dense + BM25</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#171C23] border border-[#303741]">
                <span className="text-[#9CA3AF]">Snapshot Sandbox</span>
                <span className="font-semibold text-[#34D399]">Network Egress Aborted</span>
              </div>
            </CardContent>
          </div>
          <div className="p-5 pt-0">
            <Link to="/app/findings">
              <Button variant="outline" className="w-full justify-between text-xs">
                <span>Explore All Findings</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      {/* Recent Scans Activity Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Recent Audit Scans</CardTitle>
            <CardDescription>
              Execution log of multi-page accessibility crawls and axe evaluations.
            </CardDescription>
          </div>
          <Link to="/app/scans">
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-[#38BDF8] hover:text-[#0EA5E9]">
              <span>View All Scans</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {scans.length === 0 ? (
            <div className="py-8 text-center text-sm text-[#9CA3AF]">
              No scans executed yet. Launch a scan on a verified project domain.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#303741] text-[#9CA3AF] uppercase font-semibold">
                    <th className="pb-3 font-semibold">Target URL</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold">Pages</th>
                    <th className="pb-3 font-semibold">Violations</th>
                    <th className="pb-3 font-semibold">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#303741]">
                  {scans.slice(0, 5).map((scan) => (
                    <tr key={scan.id} className="hover:bg-[#252C35]/40 transition-colors">
                      <td className="py-3 font-mono text-[#F3F4F6] font-medium max-w-xs truncate">
                        {scan.target_url}
                      </td>
                      <td className="py-3">
                        <Badge
                          variant={
                            scan.status === "completed"
                              ? "success"
                              : scan.status === "failed" || scan.status === "cancelled"
                              ? "critical"
                              : "primary"
                          }
                          className="capitalize text-[11px]"
                        >
                          {scan.status}
                        </Badge>
                      </td>
                      <td className="py-3 text-[#9CA3AF] font-mono">
                        {scan.pages_succeeded} / {scan.total_pages || scan.config?.max_pages || 1}
                      </td>
                      <td className="py-3 font-semibold font-mono text-[#FB7185]">
                        {scan.total_violations}
                      </td>
                      <td className="py-3 text-[#9CA3AF]">
                        {new Date(scan.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Observability Disclaimer Notice Banner */}
      <div className="rounded-xl border border-[#303741] bg-[#171A1F] p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-[#38BDF8] shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider">
              Observability Scope Notice
            </h4>
            <p className="text-xs text-[#9CA3AF] mt-1 leading-relaxed">
              Automated scans report automated accessibility findings detected via axe-core. Automated scans do not certify complete WCAG compliance. Assistive technology testing, manual keyboard navigation, and expert design reviews remain essential for complete conformance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
