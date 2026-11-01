import React, { useEffect, useState } from "react";

import {
  triggerInvestigation,
  getLatestInvestigation,
  InvestigationReport,
  PriorityLevel,
} from "../../api/investigations";

interface AutonomousInvestigationPanelProps {
  scanId: string;
}

export const AutonomousInvestigationPanel: React.FC<AutonomousInvestigationPanelProps> = ({
  scanId,
}) => {
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPriority, setSelectedPriority] = useState<string>("ALL");

  useEffect(() => {
    let isMounted = true;

    const fetchReport = async () => {
      try {
        const data = await getLatestInvestigation(scanId);
        if (isMounted) {
          setReport(data);
        }
      } catch {
        if (isMounted) {
          setReport(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchReport();

    return () => {
      isMounted = false;
    };
  }, [scanId]);



  const handleRunInvestigation = async () => {
    setRunning(true);
    setError(null);
    try {
      const data = await triggerInvestigation(scanId, true);
      setReport(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run autonomous investigation";
      setError(msg);
    } finally {
      setRunning(false);
    }
  };

  const getPriorityBadgeClass = (priority: PriorityLevel) => {
    switch (priority) {
      case "P1":
        return "bg-rose-950 text-rose-300 border-rose-800";
      case "P2":
        return "bg-amber-950 text-amber-300 border-amber-800";
      case "P3":
        return "bg-blue-950 text-blue-300 border-blue-800";
      case "P4":
        return "bg-slate-900 text-slate-300 border-slate-700";
      default:
        return "bg-slate-900 text-slate-300 border-slate-700";
    }
  };

  const getConfidenceBadgeClass = (confidence: string) => {
    switch (confidence) {
      case "supported":
        return "bg-emerald-950 text-emerald-300 border-emerald-800";
      case "tentative":
        return "bg-amber-950 text-amber-300 border-amber-800";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-950 text-emerald-400 border-emerald-800";
      case "partial":
        return "bg-amber-950 text-amber-400 border-amber-800";
      case "skipped":
        return "bg-purple-950 text-purple-400 border-purple-800";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading autonomous agent reports...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-base font-semibold text-slate-100">
              Autonomous Accessibility Agents
            </h3>
            {report && (
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${getConfidenceBadgeClass(
                  report.overall_confidence
                )}`}
              >
                Confidence: {report.overall_confidence.replace("_", " ")}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Five bounded specialist investigators evaluate contrast, keyboard traps, screen reader semantics, native HTML, and WCAG 2.2 criteria.
          </p>
        </div>

        <button
          onClick={handleRunInvestigation}
          disabled={running}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition disabled:opacity-50"
        >
          {running ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analyzing Dimensions...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>{report ? "Re-Run Investigation" : "Run Multi-Agent Investigation"}</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-950/50 border border-rose-800 text-sm text-rose-300">
          {error}
        </div>
      )}

      {!report && !running && (
        <div className="p-10 rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-blue-950/60 border border-blue-800 flex items-center justify-center text-blue-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h4 className="text-base font-semibold text-slate-200">No Investigation Conducted Yet</h4>
          <p className="text-sm text-slate-400 max-w-md mx-auto mt-1 mb-4">
            Execute the coordinated multi-specialist investigation to review contrast, keyboard focus traps, screen reader semantics, and normative WCAG 2.2 mappings.
          </p>
          <button
            onClick={handleRunInvestigation}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow transition"
          >
            Start Investigation Now
          </button>
        </div>
      )}

      {report && (
        <>
          {/* Executive Summary Card */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider uppercase text-blue-400">
                Coordinator Executive Synthesis
              </span>
              <span className="text-xs text-slate-500">
                {report.duration_ms !== null ? `${report.duration_ms}ms runtime` : ""}
              </span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {report.executive_summary}
            </p>
          </div>

          {/* Mandatory Enterprise Notice Alert */}
          <div className="flex items-start gap-3 p-4 rounded-xl bg-blue-950/30 border border-blue-900/60 text-blue-200">
            <svg className="w-5 h-5 mt-0.5 text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-xs leading-relaxed">
              <strong className="font-semibold text-blue-100">Assistive Technology Notice: </strong>
              The Screen Reader and Keyboard evaluations are static DOM interpretation aids and deterministic browser event runs. They do not constitute an actual NVDA, JAWS, or VoiceOver execution. Automated accessibility findings do not represent a legal WCAG compliance certification.
            </div>
          </div>

          {/* Manual Verification Checklist */}
          {report.manual_verification_checklist.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-semibold text-xs uppercase tracking-wide">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Manual Verification Checklist (Required by Specialists)</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-xs text-amber-200/90 pl-1">
                {report.manual_verification_checklist.map((item, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Specialist Agents Grid */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-200 tracking-wide">
              Specialist Agent Investigations ({Object.keys(report.specialists).length})
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(report.specialists).map(([agentId, specialist]) => (
                <div
                  key={agentId}
                  className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <h5 className="text-sm font-semibold text-slate-100">
                        {specialist.agent_name}
                      </h5>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getStatusBadgeClass(
                          specialist.status
                        )}`}
                      >
                        {specialist.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>Dimension: <span className="text-slate-300">{specialist.dimension}</span></span>
                      <span>•</span>
                      <span>Findings: <span className="text-slate-300">{specialist.findings_count}</span></span>
                    </div>

                    {specialist.status === "skipped" && (
                      <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300 space-y-1">
                        <strong className="text-purple-300 font-medium">Dimension Skipped:</strong>
                        <p className="text-slate-400">
                          {specialist.limitations[0] || "No dynamic session data recorded for this scan."}
                        </p>
                      </div>
                    )}

                    {specialist.observations.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-xs font-medium text-slate-400">Key Observations:</span>
                        <div className="space-y-1 max-h-36 overflow-y-auto pr-1 text-xs">
                          {specialist.observations.slice(0, 3).map((obs, oIdx) => (
                            <div key={oIdx} className="p-2 rounded bg-slate-950 border border-slate-800/60">
                              <span className="font-medium text-slate-200">{obs.summary}</span>
                              {obs.selector && (
                                <code className="block text-[11px] text-blue-400 truncate mt-0.5">
                                  {obs.selector}
                                </code>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {specialist.wcag_criteria.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800">
                      <span className="text-[11px] text-slate-500">WCAG 2.2:</span>
                      {specialist.wcag_criteria.map((crit, cIdx) => (
                        <span
                          key={cIdx}
                          className="text-[10px] px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/80 text-blue-300 font-mono"
                        >
                          SC {crit}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Prioritized Remediation Matrix */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <h4 className="text-sm font-semibold text-slate-200 tracking-wide">
                Prioritized Remediation Matrix ({report.remediation_matrix.length})
              </h4>
              <div className="flex items-center gap-1 p-1 bg-slate-900 rounded-lg border border-slate-800 text-xs">
                {["ALL", "P1", "P2", "P3", "P4"].map((pri) => (
                  <button
                    key={pri}
                    onClick={() => setSelectedPriority(pri)}
                    className={`px-2.5 py-1 rounded font-medium transition ${
                      selectedPriority === pri
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {pri === "ALL" ? "All Priorities" : pri}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {report.remediation_matrix
                .filter(
                  (item) => selectedPriority === "ALL" || item.priority === selectedPriority
                )
                .map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full border font-bold ${getPriorityBadgeClass(
                            item.priority
                          )}`}
                        >
                          {item.priority}
                        </span>
                        <h5 className="text-sm font-semibold text-slate-100">{item.title}</h5>
                      </div>
                      <span className="text-xs text-slate-500 font-mono">{item.dimension}</span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">{item.description}</p>

                    {item.remediation_hint && (
                      <div className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto whitespace-pre">
                        {item.remediation_hint}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
