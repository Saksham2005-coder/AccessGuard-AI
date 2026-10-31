import { Activity, AlertTriangle, CheckCircle, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";

export function OverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Accessibility Overview</h1>
        <p className="text-sm text-slate-500 mt-1">
          Automated accessibility observability, continuous scan metrics, and AI-assisted remediations.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Automated Audit Health</CardTitle>
            <Shield className="h-4 w-4 text-[#4657D8]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Automated Checks</div>
            <p className="text-xs text-slate-500 mt-1">Based on local axe-core evaluations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Active Projects</CardTitle>
            <Activity className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Verified Domains</div>
            <p className="text-xs text-slate-500 mt-1">DNS TXT ownership confirmed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Critical Findings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Action Required</div>
            <p className="text-xs text-slate-500 mt-1">WCAG Level A & AA automated failures</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Remediations</CardTitle>
            <CheckCircle className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Human Reviewed</div>
            <p className="text-xs text-slate-500 mt-1">Verified against isolated snapshots</p>
          </CardContent>
        </Card>
      </div>

      {/* Observability Disclaimer Alert (Blueprint Requirement) */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-[#4657D8] shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Observability Scope Notice</h4>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
              Automated scans report automated accessibility findings detected via axe-core. Automated scans do not certify complete WCAG compliance. Assistive technology testing, manual keyboard navigation, and expert design reviews remain essential for complete conformance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
