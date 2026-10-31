import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Download,
  FileText,
  Printer,
  ShieldCheck,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/EmptyState";
import { listProjectsApi } from "../api/projects";
import { listProjectScansApi } from "../api/scans";
import { listFindingsApi } from "../api/findings";

export function ReportsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const projects = projectsData?.items || [];
  const activeProjectId = selectedProjectId || projects[0]?.id || "";
  const activeProject = projects.find((p) => p.id === activeProjectId);

  const { data: scansData } = useQuery({
    queryKey: ["scans", activeProjectId],
    queryFn: () => listProjectScansApi(activeProjectId),
    enabled: Boolean(activeProjectId),
  });

  const { data: findingsData } = useQuery({
    queryKey: ["findings", activeProjectId],
    queryFn: () => listFindingsApi({ project_id: activeProjectId }),
    enabled: Boolean(activeProjectId),
  });

  const scans = scansData?.items || [];
  const findings = findingsData?.items || [];

  const totalViolations = findings.length;
  const criticalCount = findings.filter((f) => f.impact === "critical").length;
  const seriousCount = findings.filter((f) => f.impact === "serious").length;
  const moderateCount = findings.filter((f) => f.impact === "moderate").length;
  const minorCount = findings.filter((f) => f.impact === "minor").length;

  // Simple automated health score (100 - weighted violations, bounded 0-100)
  const penalty = criticalCount * 15 + seriousCount * 8 + moderateCount * 3 + minorCount * 1;
  const healthScore = Math.max(0, 100 - penalty);

  const handleDownloadJson = () => {
    const reportData = {
      project: activeProject,
      generated_at: new Date().toISOString(),
      standards: "WCAG 2.1 / 2.2 Level A/AA",
      audit_engine: "axe-core 4.14.0 with Playwright Chromium",
      health_score: healthScore,
      summary: {
        total_scans: scans.length,
        total_findings: totalViolations,
        critical: criticalCount,
        serious: seriousCount,
        moderate: moderateCount,
        minor: minorCount,
      },
      scans,
      findings,
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `accessguard-audit-${activeProject?.base_domain || "report"}-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  if (projectsLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading reports...</div>;
  }

  if (projects.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Export structured JSON datasets and shareable accessibility audit reports.
          </p>
        </div>
        <EmptyState
          icon={FileText}
          title="No projects configured"
          description="Create a project and execute accessibility scans to generate audit reports."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Project Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Export structured JSON datasets and shareable accessibility audit reports.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={activeProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:border-[#4657D8] focus:outline-none"
            aria-label="Select report project"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.base_domain})
              </option>
            ))}
          </select>

          <Button variant="outline" size="sm" onClick={handlePrint} className="gap-1.5 text-xs">
            <Printer className="h-4 w-4" />
            <span className="hidden sm:inline">Print Report</span>
          </Button>

          <Button size="sm" onClick={handleDownloadJson} className="gap-1.5 text-xs">
            <Download className="h-4 w-4" />
            <span>Export JSON</span>
          </Button>
        </div>
      </div>

      {/* Main Executive Summary Card */}
      <Card className="border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-bold">
                {activeProject?.name} &mdash; Accessibility Status Report
              </CardTitle>
              <CardDescription className="text-xs font-mono text-slate-400 mt-0.5">
                Target Domain: {activeProject?.base_domain} &bull; Generated: {new Date().toLocaleDateString()}
              </CardDescription>
            </div>
            <Badge variant={healthScore >= 80 ? "success" : healthScore >= 50 ? "warning" : "critical"}>
              Score: {healthScore} / 100
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-2xl font-bold text-slate-900">{scans.length}</span>
              <p className="text-xs text-slate-500 mt-1">Scans Executed</p>
            </div>
            <div className="p-4 rounded-lg bg-red-50/50 border border-red-200 text-center">
              <span className="text-2xl font-bold text-red-600">{criticalCount}</span>
              <p className="text-xs text-slate-500 mt-1">Critical Issues</p>
            </div>
            <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200 text-center">
              <span className="text-2xl font-bold text-amber-600">{seriousCount}</span>
              <p className="text-xs text-slate-500 mt-1">Serious Issues</p>
            </div>
            <div className="p-4 rounded-lg bg-blue-50/50 border border-blue-200 text-center">
              <span className="text-2xl font-bold text-blue-600">{moderateCount + minorCount}</span>
              <p className="text-xs text-slate-500 mt-1">Moderate/Minor</p>
            </div>
          </div>

          {/* Standard Evaluation Breakdown */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              WCAG Principles Evaluation
            </h3>

            <div className="rounded-lg border border-slate-200 overflow-hidden text-xs">
              <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase">
                  <tr>
                    <th className="px-4 py-2.5">Principle</th>
                    <th className="px-4 py-2.5">Coverage Focus</th>
                    <th className="px-4 py-2.5">Violations Found</th>
                    <th className="px-4 py-2.5 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-800">1. Perceivable</td>
                    <td className="px-4 py-3 text-slate-500">Text alternatives, color contrast, headings, landmarks</td>
                    <td className="px-4 py-3 font-mono font-medium">{findings.filter((f) => f.axe_rule_id.includes("color") || f.axe_rule_id.includes("alt") || f.axe_rule_id.includes("heading")).length}</td>
                    <td className="px-4 py-3 text-right"><Badge variant="outline">Evaluated</Badge></td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-800">2. Operable</td>
                    <td className="px-4 py-3 text-slate-500">Keyboard navigation, button names, link purposes</td>
                    <td className="px-4 py-3 font-mono font-medium">{findings.filter((f) => f.axe_rule_id.includes("button") || f.axe_rule_id.includes("link") || f.axe_rule_id.includes("tab")).length}</td>
                    <td className="px-4 py-3 text-right"><Badge variant="outline">Evaluated</Badge></td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-800">3. Understandable</td>
                    <td className="px-4 py-3 text-slate-500">Page language, form labels, input error announcements</td>
                    <td className="px-4 py-3 font-mono font-medium">{findings.filter((f) => f.axe_rule_id.includes("label") || f.axe_rule_id.includes("lang") || f.axe_rule_id.includes("html-has-lang")).length}</td>
                    <td className="px-4 py-3 text-right"><Badge variant="outline">Evaluated</Badge></td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-800">4. Robust</td>
                    <td className="px-4 py-3 text-slate-500">ARIA valid attribute names, roles, allowed children</td>
                    <td className="px-4 py-3 font-mono font-medium">{findings.filter((f) => f.axe_rule_id.includes("aria")).length}</td>
                    <td className="px-4 py-3 text-right"><Badge variant="outline">Evaluated</Badge></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Compliance Statement */}
          <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/75 text-xs text-slate-600 space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-slate-800">
              <ShieldCheck className="h-4 w-4 text-[#4657D8]" />
              <span>Observability Methodology & Evaluation Scope</span>
            </div>
            <p>
              Audits are conducted via headless Playwright Chromium running pinned axe-core 4.14.0 rulesets.
              Automated tests reliably catch approximately 57% of WCAG success criteria failures. All proposed AI code remediations require human reviewer approval and are verified against isolated DOM snapshots prior to production deployment.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
