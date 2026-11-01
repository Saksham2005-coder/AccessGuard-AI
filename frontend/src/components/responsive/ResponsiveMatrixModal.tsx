import React, { useState, useEffect } from 'react';
import {
  Monitor,
  Tablet,
  Smartphone,
  Layers,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { Badge } from '../ui/Badge';
import {
  ResponsiveMatrixReport,
  ViewportFindingDiff,
  getResponsiveMatrix,
  runResponsiveMatrix,
} from '../../api/responsive';

interface ResponsiveMatrixModalProps {
  isOpen: boolean;
  onClose: () => void;
  scanId: string;
  targetUrl: string;
}

export const ResponsiveMatrixModal: React.FC<ResponsiveMatrixModalProps> = ({
  isOpen,
  onClose,
  scanId,
  targetUrl,
}) => {
  const [report, setReport] = useState<ResponsiveMatrixReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recomputing, setRecomputing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedViewport, setSelectedViewport] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'all' | 'shared' | 'specific'>('all');

  const handleRecompute = async () => {
    try {
      setRecomputing(true);
      setError(null);
      const data = await runResponsiveMatrix(scanId, { force_recompute: true });
      setReport(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to evaluate responsive test matrix';
      setError(msg);
    } finally {
      setRecomputing(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !scanId) return;
    let isMounted = true;

    const loadInitialMatrix = async () => {
      try {
        const data = await getResponsiveMatrix(scanId);
        if (!isMounted) return;
        setReport(data);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Failed to evaluate responsive test matrix';
        setError(msg);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadInitialMatrix();

    return () => {
      isMounted = false;
    };
  }, [isOpen, scanId]);

  const getViewportIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'mobile':
        return <Smartphone className="w-5 h-5 text-indigo-400" />;
      case 'tablet':
        return <Tablet className="w-5 h-5 text-purple-400" />;
      default:
        return <Monitor className="w-5 h-5 text-sky-400" />;
    }
  };

  const getImpactBadgeVariant = (impact: string) => {
    switch (impact.toLowerCase()) {
      case 'critical':
        return 'critical';
      case 'serious':
        return 'serious';
      case 'moderate':
        return 'moderate';
      default:
        return 'minor';
    }
  };

  // Filter findings based on selected viewport and tab
  const getFilteredFindings = (): { shared: ViewportFindingDiff[]; specific: ViewportFindingDiff[] } => {
    if (!report) return { shared: [], specific: [] };

    let shared = report.shared_findings;
    let specific = report.viewport_specific_findings;

    if (selectedViewport !== 'all') {
      shared = shared.filter((f) => f.viewports_affected.includes(selectedViewport));
      specific = specific.filter((f) => f.viewports_affected.includes(selectedViewport));
    }

    return { shared, specific };
  };

  const { shared: filteredShared, specific: filteredSpecific } = getFilteredFindings();

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Multi-Viewport Accessibility Matrix"
      description="Compare WCAG 2.2 accessibility compliance across standard desktop, tablet, and mobile device viewports."
      className="max-w-5xl w-full"
    >
      <div className="space-y-6 max-h-[78vh] overflow-y-auto pr-1">
        {/* Header bar with target URL and Recompute button */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-neutral-900/60 rounded-xl border border-neutral-800">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Target URL:</span>
            <span className="text-sm font-mono text-neutral-200 truncate max-w-md" title={targetUrl}>
              {targetUrl}
            </span>
          </div>
          <button
            onClick={handleRecompute}
            disabled={recomputing || loading}
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50"
            data-testid="recompute-matrix-btn"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin' : ''}`} />
            {recomputing ? 'Evaluating Matrix...' : 'Re-evaluate Matrix'}
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-sm flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Error loading responsive matrix</p>
              <p className="text-xs text-red-400 mt-1">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-center">
            <RefreshCw className="w-8 h-8 text-sky-400 animate-spin mb-3" />
            <p className="text-sm text-neutral-300 font-medium">Evaluating multi-viewport accessibility matrix...</p>
            <p className="text-xs text-neutral-500 mt-1">
              Analyzing DOM reflow, touch targets, and contrast across desktop, tablet, and mobile profiles
            </p>
          </div>
        ) : report ? (
          <>
            {/* Viewport Profile Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {report.viewport_runs.map((run) => {
                const isSelected = selectedViewport === run.viewport_name;
                return (
                  <div
                    key={run.id}
                    onClick={() =>
                      setSelectedViewport(selectedViewport === run.viewport_name ? 'all' : run.viewport_name)
                    }
                    className={`cursor-pointer p-4 rounded-xl border transition-all ${
                      isSelected
                        ? 'bg-neutral-800/90 border-sky-500 ring-1 ring-sky-500/50'
                        : 'bg-neutral-900/40 border-neutral-800 hover:border-neutral-700 hover:bg-neutral-800/40'
                    }`}
                    data-testid={`viewport-card-${run.viewport_name}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {getViewportIcon(run.viewport_name)}
                        <h4 className="text-sm font-semibold text-neutral-100 capitalize">
                          {run.viewport_name}
                        </h4>
                      </div>
                      <span className="text-xs font-mono text-neutral-400">
                        {run.width}x{run.height}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-neutral-800/60 text-xs">
                      <div>
                        <span className="text-neutral-400">Total Issues:</span>
                        <span className="ml-1.5 font-semibold text-neutral-200">
                          {run.violations_count}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-400">Scale:</span>
                        <span className="ml-1.5 font-mono text-neutral-300">
                          {run.device_scale_factor}x
                        </span>
                      </div>
                      <div>
                        <span className="text-red-400">Critical:</span>
                        <span className="ml-1.5 font-semibold text-red-300">
                          {run.critical_count}
                        </span>
                      </div>
                      <div>
                        <span className="text-amber-400">Serious:</span>
                        <span className="ml-1.5 font-semibold text-amber-300">
                          {run.serious_count}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Matrix Summary Stats */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-neutral-900/40 rounded-xl border border-neutral-800 text-xs">
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-neutral-400">Cross-Viewport Violations:</span>
                  <span className="ml-1.5 font-semibold text-neutral-200 font-mono">
                    {report.total_cross_viewport_violations}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">Unique WCAG Rules:</span>
                  <span className="ml-1.5 font-semibold text-neutral-200 font-mono">
                    {report.total_unique_rules}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">Shared Across All:</span>
                  <span className="ml-1.5 font-semibold text-sky-400 font-mono">
                    {report.shared_findings.length}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">Viewport-Specific:</span>
                  <span className="ml-1.5 font-semibold text-purple-400 font-mono">
                    {report.viewport_specific_findings.length}
                  </span>
                </div>
              </div>

              {selectedViewport !== 'all' && (
                <button
                  onClick={() => setSelectedViewport('all')}
                  className="text-xs text-sky-400 hover:text-sky-300 font-medium"
                >
                  Clear Filter ({selectedViewport})
                </button>
              )}
            </div>

            {/* Filter Tabs */}
            <div className="flex border-b border-neutral-800 gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'all'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                All Findings ({filteredShared.length + filteredSpecific.length})
              </button>
              <button
                onClick={() => setActiveTab('shared')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'shared'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Shared Violations ({filteredShared.length})
              </button>
              <button
                onClick={() => setActiveTab('specific')}
                className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'specific'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-neutral-400 hover:text-neutral-200'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                Viewport-Specific Violations ({filteredSpecific.length})
              </button>
            </div>

            {/* Findings List */}
            <div className="space-y-4">
              {(activeTab === 'all' || activeTab === 'shared') && filteredShared.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-neutral-300 uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                    Shared Across All Viewports
                  </div>
                  <div className="space-y-2">
                    {filteredShared.map((finding, idx) => (
                      <div
                        key={`shared-${finding.rule_id}-${idx}`}
                        className="p-3.5 rounded-xl bg-neutral-900/50 border border-neutral-800 hover:border-neutral-700 transition-colors"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-semibold text-neutral-200">
                              {finding.rule_id}
                            </span>
                            <Badge variant={getImpactBadgeVariant(finding.impact)}>
                              {finding.impact}
                            </Badge>
                            <Badge variant="outline">
                              Omni-Viewport
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1">
                            {finding.viewports_affected.map((vp) => (
                              <span
                                key={vp}
                                className="px-2 py-0.5 rounded text-[10px] font-mono bg-neutral-800 text-neutral-300 capitalize"
                              >
                                {vp}
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-xs text-neutral-300 mb-2">{finding.description}</p>
                        <div className="bg-neutral-950 p-2 rounded-lg font-mono text-[11px] text-neutral-400 break-all border border-neutral-800/80">
                          {finding.selector}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(activeTab === 'all' || activeTab === 'specific') && filteredSpecific.length > 0 && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-purple-300 uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                    Viewport-Specific Violations (Reflow, Touch Target, or Mobile Responsive)
                  </div>
                  <div className="space-y-2">
                    {filteredSpecific.map((finding, idx) => (
                      <div
                        key={`specific-${finding.rule_id}-${idx}`}
                        className="p-3.5 rounded-xl bg-purple-950/10 border border-purple-900/30 hover:border-purple-800/50 transition-colors"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-semibold text-neutral-200">
                              {finding.rule_id}
                            </span>
                            <Badge variant={getImpactBadgeVariant(finding.impact)}>
                              {finding.impact}
                            </Badge>
                            {finding.rule_id === 'target-size' && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                WCAG 2.5.8 Touch Target
                              </span>
                            )}
                            {finding.rule_id === 'reflow' && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                WCAG 1.4.10 Reflow
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] text-neutral-400 mr-1">Only on:</span>
                            {finding.viewports_affected.map((vp) => (
                              <span
                                key={vp}
                                className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-900/50 text-purple-200 capitalize border border-purple-700/50"
                              >
                                {vp}
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-xs text-neutral-300 mb-2">{finding.description}</p>
                        <div className="bg-neutral-950 p-2 rounded-lg font-mono text-[11px] text-purple-300/80 break-all border border-neutral-800/80">
                          {finding.selector}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {filteredShared.length === 0 && filteredSpecific.length === 0 && (
                <div className="p-8 text-center rounded-xl bg-neutral-900/30 border border-neutral-800 text-neutral-400 text-xs">
                  No accessibility violations found for the selected viewport filters.
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </Dialog>
  );
};
