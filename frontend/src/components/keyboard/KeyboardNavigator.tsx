import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Keyboard,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import {
  KeyboardNavigationReport,
  KeyboardStep,
  getKeyboardTestApi,
  rerunKeyboardTestApi,
} from '../../api/keyboardTest';
import { ScanPageSummary } from '../../api/heatmap';

interface KeyboardNavigatorProps {
  scanId: string;
  pages: ScanPageSummary[];
  selectedPageId?: string;
  onSelectPage?: (pageId: string) => void;
}

export const KeyboardNavigator: React.FC<KeyboardNavigatorProps> = ({
  scanId,
  pages,
  selectedPageId,
  onSelectPage,
}) => {
  const [currentPageId, setCurrentPageId] = useState<string>(
    selectedPageId || (pages.length > 0 ? pages[0].id : '')
  );
  const [report, setReport] = useState<KeyboardNavigationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Traversal state
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1500); // ms per step
  const [activeTab, setActiveTab] = useState<'journey' | 'issues'>('journey');

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleReload = useCallback(
    async (force = false) => {
      if (!currentPageId) return;
      if (force) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        const data = force
          ? await rerunKeyboardTestApi(scanId, currentPageId)
          : await getKeyboardTestApi(scanId, currentPageId);
        setReport(data);
        setCurrentStepIndex(0);
        setIsPlaying(false);
      } catch (err: unknown) {
        const errMsg =
          err instanceof Error
            ? err.message
            : 'Failed to load keyboard navigation report';
        setError(errMsg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [scanId, currentPageId]
  );

  useEffect(() => {
    if (!currentPageId) return;
    let isMounted = true;

    getKeyboardTestApi(scanId, currentPageId)
      .then((data) => {
        if (isMounted) {
          setReport(data);
          setCurrentStepIndex(0);
          setIsPlaying(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const errMsg =
            err instanceof Error
              ? err.message
              : 'Failed to load keyboard navigation report';
          setError(errMsg);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [scanId, currentPageId]);

  const handlePageChange = (pageId: string) => {
    setCurrentPageId(pageId);
    if (onSelectPage) onSelectPage(pageId);
  };

  const steps: KeyboardStep[] = report?.steps || [];
  const currentStep: KeyboardStep | undefined = steps[currentStepIndex];

  // Auto-play stepper loop
  useEffect(() => {
    if (isPlaying && steps.length > 0) {
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isPlaying, speed, steps.length]);

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const jumpToStep = (index: number) => {
    setIsPlaying(false);
    setCurrentStepIndex(index);
    setActiveTab('journey');
  };

  if (loading && !report) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-electric-blue mb-4" />
        <p className="font-medium text-slate-200">
          Running deterministic keyboard navigation test...
        </p>
        <p className="text-sm text-slate-400 mt-1">
          Evaluating Tab focus sequence, styles, and potential keyboard traps.
        </p>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="p-6 bg-red-950/20 border border-red-800/40 rounded-xl text-center">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <p className="text-red-200 font-semibold mb-2">{error}</p>
        <button
          onClick={() => handleReload(true)}
          className="px-4 py-2 bg-red-800/40 hover:bg-red-800/60 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Retry Keyboard Test
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
        <Keyboard className="w-5 h-5 text-electric-blue shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <span className="font-semibold text-slate-100">
            Automated Keyboard Focus Simulation:
          </span>{' '}
          Executes real browser-level Tab and Shift+Tab key actions in an isolated Chromium
          sandbox. Inspects <code className="text-electric-blue">document.activeElement</code>,
          computes active focus ring styles, and flags focus traps and missing accessible names.
          Always complement automated runs with manual keyboard audits.
        </div>
      </div>

      {/* Page Selector & Run Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/40 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <label htmlFor="kb-page-select" className="text-xs font-medium text-slate-400">
            Audited Page:
          </label>
          <select
            id="kb-page-select"
            value={currentPageId}
            onChange={(e) => handlePageChange(e.target.value)}
            className="bg-slate-800 text-slate-200 text-sm rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-electric-blue"
          >
            {pages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title || p.url}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => handleReload(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-electric-blue' : ''}`} />
          {refreshing ? 'Re-running...' : 'Re-run Test'}
        </button>
      </div>

      {/* Summary KPI Cards */}
      {report && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
            <span className="text-xs font-medium text-slate-400 block mb-1">
              Focus Stops
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100">
                {report.summary.forward_steps}
              </span>
              <span className="text-xs text-slate-400">
                ({report.summary.unique_elements} unique elements)
              </span>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
            <span className="text-xs font-medium text-slate-400 block mb-1">
              Keyboard Traps
            </span>
            <div className="flex items-center gap-1.5">
              {report.summary.has_potential_trap ? (
                <>
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                  <span className="text-sm font-semibold text-red-300">Trap Detected</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-semibold text-emerald-300">No Trap Detected</span>
                </>
              )}
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
            <span className="text-xs font-medium text-slate-400 block mb-1">
              Missing Focus Ring
            </span>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-2xl font-bold ${
                  report.summary.missing_indicator_count > 0 ? 'text-amber-400' : 'text-slate-100'
                }`}
              >
                {report.summary.missing_indicator_count}
              </span>
              <span className="text-xs text-slate-400">elements</span>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
            <span className="text-xs font-medium text-slate-400 block mb-1">
              Unlabeled Controls
            </span>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-2xl font-bold ${
                  report.summary.missing_name_count > 0 ? 'text-red-400' : 'text-slate-100'
                }`}
              >
                {report.summary.missing_name_count}
              </span>
              <span className="text-xs text-slate-400">controls</span>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Traversal Player Controls */}
      {steps.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              title="Reset to Step 1"
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={handlePrev}
              disabled={currentStepIndex === 0}
              title="Previous Step"
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700 disabled:opacity-40"
            >
              <SkipBack className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              title={isPlaying ? 'Pause Traversal' : 'Play Traversal'}
              className="px-4 py-2 bg-electric-blue hover:bg-blue-600 text-white font-medium text-xs rounded-lg transition-colors flex items-center gap-1.5 shadow-sm shadow-blue-500/20"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-4 h-4" /> Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Step Auto-Play
                </>
              )}
            </button>
            <button
              onClick={handleNext}
              disabled={currentStepIndex >= steps.length - 1}
              title="Next Step"
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700 disabled:opacity-40"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          {/* Stepper info */}
          <div className="text-xs text-slate-300">
            Focus Stop <span className="font-bold text-electric-blue">{currentStepIndex + 1}</span> of{' '}
            <span className="font-bold text-slate-100">{steps.length}</span>
          </div>

          {/* Speed selector */}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Speed:</span>
            <select
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="bg-slate-800 text-slate-200 rounded px-2 py-1 border border-slate-700 text-xs focus:outline-none"
            >
              <option value={1000}>1.0s</option>
              <option value={1500}>1.5s</option>
              <option value={2000}>2.0s</option>
            </select>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        <button
          onClick={() => setActiveTab('journey')}
          className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'journey'
              ? 'border-electric-blue text-electric-blue'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Keyboard className="w-4 h-4" />
          Focus Journey ({steps.length})
        </button>
        <button
          onClick={() => setActiveTab('issues')}
          className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'issues'
              ? 'border-electric-blue text-electric-blue'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          Detected Issues ({report?.issues.length || 0})
        </button>
      </div>

      {/* Tab 1: Focus Journey & Active Element Details */}
      {activeTab === 'journey' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Step Journey List */}
          <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800 rounded-xl p-3 max-h-[500px] overflow-y-auto space-y-2">
            <span className="text-xs font-medium text-slate-400 px-2 block mb-2">
              Tab Order Sequence
            </span>

            {steps.map((st, idx) => {
              const isSelected = idx === currentStepIndex;
              return (
                <button
                  key={`${st.step_index}-${st.selector}-${idx}`}
                  onClick={() => jumpToStep(idx)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors border flex items-start gap-2.5 ${
                    isSelected
                      ? 'bg-electric-blue/10 border-electric-blue/50 text-slate-100 ring-1 ring-electric-blue/30'
                      : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:bg-slate-800/80 hover:text-slate-100'
                  }`}
                >
                  <span
                    className={`shrink-0 w-6 h-6 rounded flex items-center justify-center font-bold text-xs ${
                      isSelected
                        ? 'bg-electric-blue text-white'
                        : 'bg-slate-700/60 text-slate-300'
                    }`}
                  >
                    {st.step_index}
                  </span>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {st.tag_name}
                      </span>
                      {st.role && (
                        <span className="text-[10px] text-slate-400">role="{st.role}"</span>
                      )}
                      {!st.has_visible_focus_indicator && (
                        <span title="No visible focus ring" className="ml-auto text-amber-400">
                          <EyeOff className="w-3.5 h-3.5" />
                        </span>
                      )}
                    </div>
                    <p className="truncate text-slate-200 font-medium">
                      {st.accessible_name || (
                        <span className="italic text-red-400">No Accessible Name</span>
                      )}
                    </p>
                    <p className="truncate text-[10px] text-slate-500 font-mono mt-0.5">
                      {st.selector}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Focused Element Inspection */}
          <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
            {currentStep ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-electric-blue text-white text-xs font-bold px-2.5 py-1 rounded-md">
                      Stop #{currentStep.step_index}
                    </span>
                    <span className="font-mono text-xs uppercase px-2 py-0.5 bg-slate-800 text-slate-200 rounded border border-slate-700">
                      &lt;{currentStep.tag_name}&gt;
                    </span>
                    {currentStep.role && (
                      <span className="text-xs text-slate-400">role="{currentStep.role}"</span>
                    )}
                  </div>

                  {currentStep.has_visible_focus_indicator ? (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2 py-0.5 rounded">
                      <Eye className="w-3.5 h-3.5" /> Visible Focus Ring
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-950/30 border border-amber-800/40 px-2 py-0.5 rounded">
                      <EyeOff className="w-3.5 h-3.5" /> No Discernible Focus Ring
                    </span>
                  )}
                </div>

                {/* Accessible Name */}
                <div>
                  <span className="text-xs font-medium text-slate-400 block mb-1">
                    Computed Accessible Name
                  </span>
                  <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60 text-sm">
                    {currentStep.accessible_name ? (
                      <span className="text-slate-100 font-medium">
                        "{currentStep.accessible_name}"
                      </span>
                    ) : (
                      <div className="flex items-center gap-2 text-red-300 font-medium">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        Missing Accessible Name (WCAG 4.1.2)
                      </div>
                    )}
                  </div>
                </div>

                {/* Selector */}
                <div>
                  <span className="text-xs font-medium text-slate-400 block mb-1">
                    DOM Target Selector
                  </span>
                  <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 break-all select-all">
                    {currentStep.selector}
                  </div>
                </div>

                {/* Focus Styling Evidence */}
                <div>
                  <span className="text-xs font-medium text-slate-400 block mb-1">
                    Computed Focus Style Evidence
                  </span>
                  {currentStep.focus_style ? (
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                      <div>
                        <span className="text-slate-500 block">outline-style:</span>
                        <span className="text-slate-200">
                          {currentStep.focus_style.outline_style}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">outline-width:</span>
                        <span className="text-slate-200">
                          {currentStep.focus_style.outline_width}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">outline-color:</span>
                        <span className="text-slate-200 truncate block">
                          {currentStep.focus_style.outline_color || '(none)'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">box-shadow:</span>
                        <span className="text-slate-200 truncate block">
                          {currentStep.focus_style.box_shadow || '(none)'}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-400 italic">
                      Style information unavailable for this node.
                    </div>
                  )}
                </div>

                {/* Additional Properties */}
                <div className="flex flex-wrap gap-4 text-xs pt-2 border-t border-slate-800">
                  <div>
                    <span className="text-slate-400">Tabindex: </span>
                    <span
                      className={`font-mono font-semibold ${
                        (currentStep.tabindex ?? 0) > 0 ? 'text-amber-400' : 'text-slate-200'
                      }`}
                    >
                      {currentStep.tabindex !== null ? currentStep.tabindex : '(natural flow)'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400">Position: </span>
                    <span className="text-slate-200">
                      {currentStep.is_clipped_or_offscreen ? (
                        <span className="text-amber-400 font-medium">Offscreen / Clipped</span>
                      ) : (
                        'In Viewport'
                      )}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-slate-400 text-sm">
                No step selected or no focusable elements found on this page.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Detected Issues List */}
      {activeTab === 'issues' && (
        <div className="space-y-3">
          {report?.issues && report.issues.length > 0 ? (
            report.issues.map((issue, idx) => {
              const isTrap = issue.issue_type === 'potential_focus_trap';
              const isMissingName = issue.issue_type === 'missing_accessible_name';

              return (
                <div
                  key={`${issue.issue_type}-${idx}`}
                  className={`p-4 rounded-xl border transition-all ${
                    isTrap
                      ? 'bg-red-950/20 border-red-800/40 text-red-200'
                      : isMissingName
                      ? 'bg-amber-950/20 border-amber-800/40 text-amber-200'
                      : 'bg-slate-900/60 border-slate-800 text-slate-200'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                          issue.severity === 'critical'
                            ? 'bg-red-900/60 text-red-300 border border-red-700/60'
                            : issue.severity === 'serious'
                            ? 'bg-amber-900/60 text-amber-300 border border-amber-700/60'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {issue.severity}
                      </span>
                      <span className="font-semibold text-sm text-slate-100">
                        {issue.message}
                      </span>
                    </div>

                    {issue.step_index !== null && issue.step_index !== undefined && (
                      <button
                        onClick={() => jumpToStep(issue.step_index! - 1)}
                        className="text-xs font-medium text-electric-blue hover:text-blue-400 flex items-center gap-1"
                      >
                        Jump to Step #{issue.step_index}
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 mb-2 leading-relaxed">
                    <span className="font-medium text-slate-200">Recommendation: </span>
                    {issue.recommendation}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/60 text-xs">
                    <span className="font-mono text-[11px] text-slate-400 truncate max-w-md">
                      {issue.selector}
                    </span>
                    <div className="flex gap-1.5">
                      {issue.wcag_criteria.map((wcag) => (
                        <span
                          key={wcag}
                          className="px-2 py-0.5 bg-slate-800 rounded text-[10px] text-slate-300 border border-slate-700"
                        >
                          {wcag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="font-semibold text-slate-200">No Keyboard Defects Detected</p>
              <p className="text-xs text-slate-400 mt-1">
                Tab order, accessible labels, and focus indicators satisfied automated checks.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
