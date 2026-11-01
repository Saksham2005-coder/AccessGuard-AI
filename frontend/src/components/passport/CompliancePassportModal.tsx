import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  FileCheck2,
  Copy,
  Check,
  Download,
  FileText,
  RefreshCw,
  AlertTriangle,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { Badge } from '../ui/Badge';
import {
  CompliancePassportDetail,
  CompliancePassportSummary,
  listProjectPassports,
  getProjectPassport,
  generateProjectPassport,
  exportProjectPassportDocument,
} from '../../api/passport';

interface CompliancePassportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  baseDomain: string;
}

export const CompliancePassportModal: React.FC<CompliancePassportModalProps> = ({
  isOpen,
  onClose,
  projectId,
  projectName,
  baseDomain,
}) => {
  const [passports, setPassports] = useState<CompliancePassportSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [detail, setDetail] = useState<CompliancePassportDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'telemetry' | 'wcag' | 'checklist'>('overview');
  const [markdownView, setMarkdownView] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !projectId) return;
    let isMounted = true;

    const loadPassports = async () => {
      try {
        const list = await listProjectPassports(projectId);
        if (!isMounted) return;
        setPassports(list);
        if (list.length > 0) {
          const latestId = list[0].id;
          setSelectedId(latestId);
          const fullDetail = await getProjectPassport(projectId, latestId);
          if (!isMounted) return;
          setDetail(fullDetail);
        } else {
          // Auto-generate v1 if none exists
          const created = await generateProjectPassport(projectId);
          if (!isMounted) return;
          setPassports([
            {
              id: created.id,
              project_id: created.project_id,
              version: created.version,
              status: created.status,
              integrity_hash: created.integrity_hash,
              status_label: created.evidence_payload.compliance_evaluation.status_label,
              total_scans_included: created.evidence_payload.audit_scope.total_scans_included,
              total_violations: created.evidence_payload.compliance_evaluation.total_violations,
              created_at: created.created_at,
            },
          ]);
          setSelectedId(created.id);
          setDetail(created);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Failed to load compliance passport';
        setError(msg);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadPassports();

    return () => {
      isMounted = false;
    };
  }, [isOpen, projectId]);

  const handleSelectVersion = async (passportId: string) => {
    try {
      setSelectedId(passportId);
      setLoading(true);
      setError(null);
      const data = await getProjectPassport(projectId, passportId);
      setDetail(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve passport version';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNewVersion = async () => {
    try {
      setGenerating(true);
      setError(null);
      const created = await generateProjectPassport(projectId);
      const updatedList = await listProjectPassports(projectId);
      setPassports(updatedList);
      setSelectedId(created.id);
      setDetail(created);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate new passport version';
      setError(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyHash = () => {
    if (!detail) return;
    navigator.clipboard.writeText(detail.integrity_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleDownloadJson = () => {
    if (!detail) return;
    const blob = new Blob([JSON.stringify(detail.evidence_payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `compliance-passport-${detail.version}-${baseDomain}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportDocument = async () => {
    if (!detail) return;
    try {
      const doc = await exportProjectPassportDocument(projectId, detail.id);
      setMarkdownView(doc.markdown_content);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to export document';
      setError(msg);
    }
  };

  const getStatusBadge = (statusLabel: string) => {
    if (statusLabel.includes('No automated findings')) {
      return <Badge variant="success">{statusLabel}</Badge>;
    }
    if (statusLabel.includes('Outstanding')) {
      return <Badge variant="warning">{statusLabel}</Badge>;
    }
    return <Badge variant="critical">{statusLabel}</Badge>;
  };

  const payload = detail?.evidence_payload;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Accessibility Compliance Passport"
      description={`Versioned, cryptographically hashed evidence package for ${projectName} (${baseDomain}).`}
      className="max-w-5xl w-full"
    >
      <div className="space-y-5 max-h-[78vh] overflow-y-auto pr-1">
        {/* Strict Legal Non-Certification Disclaimer Banner */}
        <div className="p-3.5 rounded-xl bg-sky-950/20 border border-sky-800/40 text-xs flex items-start gap-3 text-sky-200">
          <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-sky-100">Engineering Audit & Governance Notice: </span>
            This compliance passport is an auditable record of automated testing and engineering evidence.
            It is <span className="underline font-semibold">not an official WCAG legal certification</span> or
            guarantee of non-liability.
          </div>
        </div>

        {/* Top Controls: Version Switcher & Generate Action */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-neutral-900/60 rounded-xl border border-neutral-800">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-neutral-400">Passport Version:</span>
            <div className="relative">
              <select
                value={selectedId}
                onChange={(e) => handleSelectVersion(e.target.value)}
                disabled={loading || generating}
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500 font-mono"
                data-testid="passport-version-select"
              >
                {passports.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.version} — {new Date(p.created_at).toLocaleDateString()} ({p.status_label})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateNewVersion}
              disabled={generating || loading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50"
              data-testid="generate-passport-btn"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
              {generating ? 'Generating Snapshot...' : 'Generate New Version'}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-center">
            <RefreshCw className="w-8 h-8 text-sky-400 animate-spin mb-3" />
            <p className="text-sm text-neutral-300 font-medium">Loading compliance passport evidence...</p>
          </div>
        ) : detail && payload ? (
          <>
            {/* Manifest Integrity Bar */}
            <div className="p-3.5 bg-neutral-900/40 rounded-xl border border-neutral-800 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-neutral-400">SHA-256 Checksum:</span>
                <span className="font-mono text-[11px] text-sky-300 bg-sky-950/40 border border-sky-800/50 px-2 py-0.5 rounded max-w-sm truncate" title={detail.integrity_hash}>
                  {detail.integrity_hash}
                </span>
                <button
                  onClick={handleCopyHash}
                  className="p-1 text-neutral-400 hover:text-neutral-200 transition-colors"
                  title="Copy SHA-256 hash"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-neutral-400">Audit Status:</span>
                {getStatusBadge(payload.compliance_evaluation.status_label)}
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-neutral-800 gap-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'overview'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Overview & Scope
              </button>
              <button
                onClick={() => setActiveTab('telemetry')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'telemetry'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Multi-Engine Telemetry
              </button>
              <button
                onClick={() => setActiveTab('wcag')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'wcag'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <FileCheck2 className="w-3.5 h-3.5" />
                WCAG 2.2 Criteria ({payload.wcag_criteria_audited.length})
              </button>
              <button
                onClick={() => setActiveTab('checklist')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'checklist'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Manual Review Checklist
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'overview' && (
              <div className="space-y-4">
                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-neutral-900/50 rounded-xl border border-neutral-800">
                    <span className="text-[11px] text-neutral-400 uppercase tracking-wider">Scans Included</span>
                    <p className="text-xl font-bold font-mono text-neutral-100 mt-1">
                      {payload.audit_scope.total_scans_included}
                    </p>
                    <p className="text-[10px] text-neutral-500 mt-0.5">
                      {payload.audit_scope.total_pages_audited} pages audited
                    </p>
                  </div>
                  <div className="p-3 bg-neutral-900/50 rounded-xl border border-neutral-800">
                    <span className="text-[11px] text-neutral-400 uppercase tracking-wider">Total Violations</span>
                    <p className="text-xl font-bold font-mono text-neutral-100 mt-1">
                      {payload.compliance_evaluation.total_violations}
                    </p>
                    <p className="text-[10px] text-neutral-500 mt-0.5">
                      {payload.compliance_evaluation.unique_wcag_rules_flagged.length} unique rules
                    </p>
                  </div>
                  <div className="p-3 bg-neutral-900/50 rounded-xl border border-neutral-800">
                    <span className="text-[11px] text-red-400 uppercase tracking-wider">Critical / Serious</span>
                    <p className="text-xl font-bold font-mono text-red-300 mt-1">
                      {payload.compliance_evaluation.severity_breakdown.critical +
                        payload.compliance_evaluation.severity_breakdown.serious}
                    </p>
                    <p className="text-[10px] text-neutral-500 mt-0.5">
                      {payload.compliance_evaluation.severity_breakdown.critical} critical,{' '}
                      {payload.compliance_evaluation.severity_breakdown.serious} serious
                    </p>
                  </div>
                  <div className="p-3 bg-neutral-900/50 rounded-xl border border-neutral-800">
                    <span className="text-[11px] text-emerald-400 uppercase tracking-wider">Remediations</span>
                    <p className="text-xl font-bold font-mono text-emerald-300 mt-1">
                      {payload.compliance_evaluation.remediations_summary.resolved_or_verified}
                    </p>
                    <p className="text-[10px] text-neutral-500 mt-0.5">
                      {payload.compliance_evaluation.remediations_summary.pending_or_proposed} in review
                    </p>
                  </div>
                </div>

                {/* Scope details */}
                <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800 text-xs space-y-2">
                  <h4 className="font-semibold text-neutral-200">Audit Scope & Environment</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-neutral-400">
                    <div>
                      <span>Engine: </span>
                      <span className="text-neutral-200 font-medium">{payload.audit_scope.scanner_engine}</span>
                    </div>
                    <div>
                      <span>axe-core Version: </span>
                      <span className="text-neutral-200 font-mono">{payload.audit_scope.axe_version}</span>
                    </div>
                    <div>
                      <span>Target Base Domain: </span>
                      <span className="text-neutral-200 font-mono">{baseDomain}</span>
                    </div>
                    <div>
                      <span>Timestamp: </span>
                      <span className="text-neutral-200">{new Date(detail.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'telemetry' && (
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-neutral-900/50 border border-neutral-800 text-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-neutral-200">Responsive Multi-Viewport Matrix</span>
                    <Badge variant="outline">
                      {payload.multi_engine_evidence.multi_viewport_testing.runs_recorded} Runs
                    </Badge>
                  </div>
                  <p className="text-neutral-400 mb-2">
                    Audited viewports:{' '}
                    {payload.multi_engine_evidence.multi_viewport_testing.viewports_tested.join(', ') ||
                      'Desktop, Tablet, Mobile'}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-neutral-900/50 border border-neutral-800 text-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-neutral-200">Keyboard Navigation Simulator</span>
                    <Badge variant="success">Active</Badge>
                  </div>
                  <p className="text-neutral-400">
                    {payload.multi_engine_evidence.keyboard_simulator.status}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-neutral-900/50 border border-neutral-800 text-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-neutral-200">Screen Reader Semantic Preview</span>
                    <Badge variant="success">Active</Badge>
                  </div>
                  <p className="text-neutral-400">
                    {payload.multi_engine_evidence.screen_reader_preview.status}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-neutral-900/50 border border-neutral-800 text-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-neutral-200">Historical Regression Baseline</span>
                    <Badge variant="outline">
                      {payload.multi_engine_evidence.regression_monitoring.baseline_pinned ? 'Pinned' : 'None'}
                    </Badge>
                  </div>
                  <p className="text-neutral-400">
                    Baseline Scan ID:{' '}
                    <span className="font-mono text-neutral-300">
                      {payload.multi_engine_evidence.regression_monitoring.baseline_scan_id || 'N/A'}
                    </span>
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'wcag' && (
              <div className="space-y-2">
                {payload.wcag_criteria_audited.map((c) => (
                  <div
                    key={c.criterion_id}
                    className="p-3 rounded-xl bg-neutral-900/40 border border-neutral-800 text-xs flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-sky-400">WCAG {c.criterion_id}</span>
                        <span className="font-medium text-neutral-200">{c.title}</span>
                        <Badge variant="outline">Level {c.level}</Badge>
                      </div>
                      <p className="text-[11px] text-neutral-400 mt-1">{c.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'checklist' && (
              <div className="space-y-2.5">
                {payload.manual_review_checklist.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-neutral-900/40 border border-neutral-800 text-xs"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-semibold text-neutral-200">{item.item}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/50">
                        {item.status}
                      </span>
                    </div>
                    <p className="text-neutral-400 text-[11px] mb-1">{item.notes}</p>
                    <span className="text-[10px] font-mono text-sky-400">{item.guideline}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Bottom Export Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-neutral-800">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadJson}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 transition-colors border border-neutral-700"
                  data-testid="download-passport-json-btn"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON Evidence
                </button>
                <button
                  onClick={handleExportDocument}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 transition-colors border border-neutral-700"
                  data-testid="view-markdown-btn"
                >
                  <FileText className="w-3.5 h-3.5" />
                  View Audit Document
                </button>
              </div>

              <button
                onClick={onClose}
                className="px-4 py-1.5 text-xs font-medium rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 transition-colors"
              >
                Close
              </button>
            </div>
          </>
        ) : null}

        {/* Markdown Document Preview Modal */}
        {markdownView && (
          <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-neutral-200">Audit Document Preview</span>
              <button
                onClick={() => setMarkdownView(null)}
                className="text-xs text-neutral-400 hover:text-neutral-200"
              >
                Hide
              </button>
            </div>
            <pre className="p-3 bg-neutral-900 rounded-lg text-[11px] font-mono text-neutral-300 overflow-x-auto max-h-60 whitespace-pre-wrap">
              {markdownView}
            </pre>
          </div>
        )}
      </div>
    </Dialog>
  );
};
