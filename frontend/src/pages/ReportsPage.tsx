import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Download,
  FileText,
  Printer,
  Shield,
  ShieldCheck,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/EmptyState";
import { listProjectsApi } from "../api/projects";
import { listProjectScansApi } from "../api/scans";
import { listFindingsApi } from "../api/findings";
import { CompliancePassportModal } from "../components/passport/CompliancePassportModal";

export function ReportsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [isPassportOpen, setIsPassportOpen] = useState(false);

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
  const completedScans = scans.filter((s) => s.status === "completed");
  const hasCompletedScans = completedScans.length > 0;

  const totalViolations = findings.length;
  const criticalCount = findings.filter((f) => f.impact === "critical").length;
  const seriousCount = findings.filter((f) => f.impact === "serious").length;
  const moderateCount = findings.filter((f) => f.impact === "moderate").length;
  const minorCount = findings.filter((f) => f.impact === "minor").length;

  // Simple automated health score (100 - weighted violations, bounded 0-100)
  const penalty = criticalCount * 15 + seriousCount * 8 + moderateCount * 3 + minorCount * 1;
  const healthScore = hasCompletedScans ? Math.max(0, 100 - penalty) : null;

  const handleDownloadJson = () => {
    const reportData = {
      project: activeProject,
      generated_at: new Date().toISOString(),
      standards: "WCAG 2.1 / 2.2 Level A/AA",
      audit_engine: "axe-core 4.14.0 with Playwright Chromium",
      health_score: healthScore,
      health_score_status: hasCompletedScans ? "assessed" : "not_yet_assessed",
      summary: {
        total_scans: scans.length,
        completed_scans: completedScans.length,
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

  const sanitizeCsvField = (value: string | number | null | undefined): string => {
    if (value === null || value === undefined) return '""';
    let str = String(value);
    // Neutralize formula injection in spreadsheet software
    if (/^[=+\-@\t\r]/.test(str)) {
      str = `'${str}`;
    }
    str = str.replace(/"/g, '""');
    return `"${str}"`;
  };

  const handleDownloadCsv = () => {
    const headers = [
      "Rule ID",
      "Impact",
      "Description",
      "Help",
      "Help URL",
      "Target / Selector",
      "Scan Page ID",
    ];
    const rows = findings.map((f) => [
      sanitizeCsvField(f.axe_rule_id),
      sanitizeCsvField(f.impact),
      sanitizeCsvField(f.description),
      sanitizeCsvField(f.help),
      sanitizeCsvField(f.help_url),
      sanitizeCsvField(f.selector),
      sanitizeCsvField(f.scan_page_id),
    ]);
    const csvContent = [headers.map(sanitizeCsvField).join(","), ...rows.map((r) => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `accessguard-audit-${activeProject?.base_domain || "report"}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  if (projectsLoading) {
    return <div className="p-8 text-center text-sm text-[#9CA3AF]">Loading compliance reports...</div>;
  }

  if (projects.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">Audit Reports</h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Export structured JSON datasets and shareable accessibility audit reports.
          </p>
        </div>
        <EmptyState
          icon={FileText}
          title="No Projects Available for Reporting"
          description="Create a monitored project and run an audit scan to generate executive accessibility reports."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Export Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            Audit Reports
          </h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Export structured JSON datasets and shareable accessibility audit reports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={activeProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="h-9 rounded-lg border border-[#303741] bg-[#171C23] px-3 text-xs font-medium text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors cursor-pointer"
            aria-label="Filter report by project"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id} className="bg-[#1D2229]">
                {p.name} ({p.base_domain})
              </option>
            ))}
          </select>

          <Button variant="outline" size="sm" onClick={handleDownloadCsv} className="gap-1.5 text-xs">
            <Download className="h-3.5 w-3.5 text-emerald-400" />
            <span>Download CSV</span>
          </Button>

          <Button variant="outline" size="sm" onClick={handleDownloadJson} className="gap-1.5 text-xs">
            <Download className="h-3.5 w-3.5 text-[#38BDF8]" />
            <span>Download JSON</span>
          </Button>

          <Button size="sm" onClick={handlePrint} className="gap-1.5 text-xs font-semibold">
            <Printer className="h-3.5 w-3.5" />
            <span>Print Report</span>
          </Button>

          <Button
            size="sm"
            onClick={() => setIsPassportOpen(true)}
            className="gap-1.5 text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white"
            data-testid="open-passport-btn"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Compliance Passport</span>
          </Button>
        </div>
      </div>

      {/* Executive Health Score Banner */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-[#171A1F] to-[#1D2229] p-6 border-b border-[#303741]">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#38BDF8]">
                  Automated Audit Health Score
                </span>
                <Badge variant="outline" className="text-[10px] font-mono border-[#38BDF8]/30 text-[#38BDF8]">
                  axe-core 4.14.0
                </Badge>
              </div>
              <h2 className="text-xl font-bold text-[#F3F4F6]">
                {activeProject?.name} ({activeProject?.base_domain})
              </h2>
              <p className="text-xs text-[#9CA3AF] max-w-xl leading-relaxed">
                Aggregated automated score based on rule violations detected during continuous crawling. Note: Automated scans do not certify legal WCAG compliance.
              </p>
            </div>

            <div className="flex items-center gap-4 bg-[#111315] border border-[#303741] rounded-2xl p-4 shrink-0">
              <div className="text-right">
                <div className="text-xs text-[#9CA3AF] font-medium">Health Score</div>
                <div className="text-xs text-[#6B7280]">
                  {hasCompletedScans ? "Out of 100 max" : "Not yet assessed"}
                </div>
              </div>
              <div className="text-3xl font-extrabold font-mono text-[#38BDF8]">
                {hasCompletedScans ? healthScore : "N/A"}
              </div>
            </div>
          </div>
        </div>

        <CardContent className="p-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3.5">
              <div className="text-xs font-medium text-[#FB7185]">Critical Issues</div>
              <div className="text-2xl font-bold font-mono text-[#FB7185] mt-1">{criticalCount}</div>
            </div>
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3.5">
              <div className="text-xs font-medium text-orange-400">Serious Violations</div>
              <div className="text-2xl font-bold font-mono text-orange-400 mt-1">{seriousCount}</div>
            </div>
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3.5">
              <div className="text-xs font-medium text-[#FBBF24]">Moderate Violations</div>
              <div className="text-2xl font-bold font-mono text-[#FBBF24] mt-1">{moderateCount}</div>
            </div>
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3.5">
              <div className="text-xs font-medium text-[#38BDF8]">Minor Violations</div>
              <div className="text-2xl font-bold font-mono text-[#38BDF8] mt-1">{minorCount}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* WCAG Principles (POUR) Grid */}
      <div className="space-y-3">
        <h3 className="text-base font-semibold text-[#F3F4F6]">
          WCAG 2.2 Principles Breakdown
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#F3F4F6]">1. Perceivable</span>
              <Badge variant="outline" className="text-[10px]">Info & UI</Badge>
            </div>
            <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
              Text alternatives, time-based media, adaptable structure, and distinguishable contrast.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#F3F4F6]">2. Operable</span>
              <Badge variant="outline" className="text-[10px]">Navigation</Badge>
            </div>
            <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
              Keyboard accessible, enough time, seizures prevention, navigability, and input modalities.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#F3F4F6]">3. Understandable</span>
              <Badge variant="outline" className="text-[10px]">Clarity</Badge>
            </div>
            <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
              Readable text language, predictable web pages, and automated input assistance.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[#F3F4F6]">4. Robust</span>
              <Badge variant="outline" className="text-[10px]">Compatibility</Badge>
            </div>
            <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
              Compatible with current and future user agents, including assistive technologies.
            </p>
          </Card>
        </div>
      </div>

      {/* Observability Boundary Disclaimer */}
      <div className="rounded-xl border border-[#303741] bg-[#171A1F] p-4 text-xs">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-[#38BDF8] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-[#F3F4F6] uppercase tracking-wider text-[11px]">
              Compliance Notice
            </span>
            <p className="text-[#9CA3AF] mt-0.5 leading-relaxed">
              Automated scans cover objective criteria (contrast, alt attributes, ARIA roles, form labels). True accessibility conformance requires expert manual verification, screen reader testing (NVDA, VoiceOver), and assistive technology assessments.
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Passport Modal */}
      {activeProject && (
        <CompliancePassportModal
          isOpen={isPassportOpen}
          onClose={() => setIsPassportOpen(false)}
          projectId={activeProject.id}
          projectName={activeProject.name}
          baseDomain={activeProject.base_domain}
        />
      )}
    </div>
  );
}
