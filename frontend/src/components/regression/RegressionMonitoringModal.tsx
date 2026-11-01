import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  History,
  Pin,
  Calendar,
  Clock,
  Trash2,
  Play,
  Pause,
  RefreshCw,
  Info,
  ShieldAlert,
  Plus,
} from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { Badge } from '../ui/Badge';
import {
  RegressionComparisonReport,
  ProjectBaselineResponse,
  ScanScheduleResponse,
  compareScanRegressionApi,
  getProjectBaselineApi,
  setProjectBaselineApi,
  listScanSchedulesApi,
  createScanScheduleApi,
  toggleScanScheduleApi,
  deleteScanScheduleApi,
} from '../../api/regression';
import { Scan } from '../../api/scans';

interface RegressionMonitoringModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  currentScan: Scan;
  availableScans: Scan[];
}

export const RegressionMonitoringModal: React.FC<RegressionMonitoringModalProps> = ({
  isOpen,
  onClose,
  projectId,
  currentScan,
  availableScans,
}) => {
  const [activeTab, setActiveTab] = useState<'regression' | 'schedules'>('regression');
  const [selectedBaselineId, setSelectedBaselineId] = useState<string>('');
  const [baselineInfo, setBaselineInfo] = useState<ProjectBaselineResponse | null>(null);
  const [report, setReport] = useState<RegressionComparisonReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Findings filter
  const [filterClass, setFilterClass] = useState<
    'all' | 'new' | 'resolved' | 'persistent' | 'changed' | 'inconclusive'
  >('all');

  // Pin baseline state
  const [pinning, setPinning] = useState<boolean>(false);
  const [pinNotes, setPinNotes] = useState<string>('');
  const [showPinDialog, setShowPinDialog] = useState<boolean>(false);

  // Schedules state
  const [schedules, setSchedules] = useState<ScanScheduleResponse[]>([]);
  const [schedulesLoading, setSchedulesLoading] = useState<boolean>(false);
  const [newCadence, setNewCadence] = useState<string>('weekly');
  const [newTargetUrl, setNewTargetUrl] = useState<string>(currentScan.target_url);
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  const handleReloadReport = async () => {
    if (!projectId || !currentScan?.id) return;
    setLoading(true);
    setError(null);

    try {
      const pinned = await getProjectBaselineApi(projectId);
      setBaselineInfo(pinned);

      const baselineId = selectedBaselineId || (pinned ? pinned.scan_id : undefined);
      const rep = await compareScanRegressionApi(projectId, currentScan.id, baselineId);
      setReport(rep);
      if (!selectedBaselineId) {
        setSelectedBaselineId(rep.baseline_scan_id);
      }
    } catch (err: unknown) {
      const errMsg =
        err instanceof Error ? err.message : 'Failed to generate regression report';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !projectId || !currentScan?.id) return;
    let isMounted = true;

    const fetchData = async () => {
      try {
        const pinned = await getProjectBaselineApi(projectId);
        if (!isMounted) return;
        setBaselineInfo(pinned);

        const baselineId = selectedBaselineId || (pinned ? pinned.scan_id : undefined);
        const rep = await compareScanRegressionApi(projectId, currentScan.id, baselineId);
        if (!isMounted) return;
        setReport(rep);
        if (!selectedBaselineId) {
          setSelectedBaselineId(rep.baseline_scan_id);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const errMsg =
          err instanceof Error ? err.message : 'Failed to generate regression report';
        setError(errMsg);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [isOpen, projectId, currentScan?.id, selectedBaselineId]);

  useEffect(() => {
    if (!isOpen || !projectId) return;
    let isMounted = true;

    listScanSchedulesApi(projectId)
      .then((list) => {
        if (isMounted) {
          setSchedules(list);
          setSchedulesLoading(false);
        }
      })
      .catch((err: unknown) => {
        console.error('Failed to load schedules', err);
        if (isMounted) {
          setSchedulesLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, projectId]);

  const handlePinBaseline = async () => {
    setPinning(true);
    try {
      const pinned = await setProjectBaselineApi(projectId, currentScan.id, pinNotes);
      setBaselineInfo(pinned);
      setShowPinDialog(false);
      setPinNotes('');
      await handleReloadReport();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to pin baseline');
    } finally {
      setPinning(false);
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setScheduleError(null);
    try {
      const created = await createScanScheduleApi(projectId, {
        cadence: newCadence,
        target_url: newTargetUrl,
        notify_on_regression: true,
      });
      setSchedules((prev) => [created, ...prev]);
    } catch (err: unknown) {
      setScheduleError(
        err instanceof Error ? err.message : 'Failed to create schedule'
      );
    }
  };

  const handleToggleSchedule = async (scheduleId: string, currentActive: boolean) => {
    try {
      const updated = await toggleScanScheduleApi(projectId, scheduleId, !currentActive);
      setSchedules((prev) => prev.map((s) => (s.id === scheduleId ? updated : s)));
    } catch (err: unknown) {
      console.error('Failed to toggle schedule', err);
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    try {
      await deleteScanScheduleApi(projectId, scheduleId);
      setSchedules((prev) => prev.filter((s) => s.id !== scheduleId));
    } catch (err: unknown) {
      console.error('Failed to delete schedule', err);
    }
  };

  const filteredFindings =
    report?.findings.filter((f) => {
      if (filterClass === 'all') return true;
      return f.classification === filterClass;
    }) || [];

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Accessibility Regression Monitoring"
      description={`Compare audit results against baseline, detect regressions, and schedule recurring audits for ${currentScan.target_url}`}
      className="max-w-5xl"
    >
      <div className="space-y-5 pt-2">
        {/* Navigation Tabs */}
        <div className="flex border-b border-[#303741] pb-2 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('regression')}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === 'regression'
                ? 'bg-[#252C35] text-[#38BDF8]'
                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
            }`}
          >
            <History className="h-4 w-4" />
            <span>Regression Analysis</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('schedules')}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === 'schedules'
                ? 'bg-[#252C35] text-[#38BDF8]'
                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
            }`}
          >
            <Calendar className="h-4 w-4" />
            <span>Scheduled Audits ({schedules.length})</span>
          </button>
        </div>

        {activeTab === 'regression' && (
          <div className="space-y-5">
            {/* Disclaimer Banner */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex items-start gap-3">
              <Info className="w-5 h-5 text-electric-blue shrink-0 mt-0.5" />
              <div className="text-xs text-slate-300 leading-relaxed">
                <span className="font-semibold text-slate-100">
                  Coverage-Aware Historical Regression Analysis:
                </span>{' '}
                Findings are matched across scans using deterministic, versioned fingerprints (
                <code className="text-electric-blue">v1</code>). Findings on pages missing from the
                current scan are classified as <strong>Inconclusive</strong> rather than falsely
                marked resolved. Automated results do not constitute legal WCAG compliance.
              </div>
            </div>

            {/* Baseline Configuration Controls */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/40 p-3.5 rounded-xl border border-slate-800">
              <div className="flex flex-wrap items-center gap-3">
                <label
                  htmlFor="baseline-scan-select"
                  className="text-xs font-medium text-slate-400"
                >
                  Comparison Baseline:
                </label>
                <select
                  id="baseline-scan-select"
                  value={selectedBaselineId}
                  onChange={(e) => {
                    setSelectedBaselineId(e.target.value);
                  }}
                  className="bg-slate-800 text-slate-200 text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-electric-blue"
                >
                  {availableScans
                    .filter((s) => s.id !== currentScan.id && s.status === 'completed')
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        Scan {s.id.slice(0, 8)} • {s.total_violations} issues •{' '}
                        {new Date(s.created_at).toLocaleDateString()}
                        {baselineInfo?.scan_id === s.id ? ' [PINNED BASELINE]' : ''}
                      </option>
                    ))}
                </select>

                {baselineInfo?.scan_id === report?.baseline_scan_id && (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-electric-blue bg-blue-950/40 border border-blue-800/40 px-2 py-0.5 rounded">
                    <Pin className="w-3 h-3" /> Pinned Project Baseline
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowPinDialog(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
                >
                  <Pin className="w-3.5 h-3.5 text-electric-blue" />
                  Pin This Scan as Baseline
                </button>
                <button
                  type="button"
                  onClick={handleReloadReport}
                  disabled={loading}
                  className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Pin Baseline Dialog */}
            {showPinDialog && (
              <div className="p-4 bg-slate-900 border border-electric-blue/40 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                    <Pin className="w-4 h-4 text-electric-blue" />
                    Pin Current Scan as Project Baseline
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPinDialog(false)}
                    className="text-slate-400 hover:text-slate-200 text-xs"
                  >
                    Cancel
                  </button>
                </div>
                <input
                  type="text"
                  placeholder="Optional baseline description / notes (e.g. v2.0 Release Candidate audit)"
                  value={pinNotes}
                  onChange={(e) => setPinNotes(e.target.value)}
                  className="w-full bg-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:border-electric-blue"
                />
                <button
                  type="button"
                  onClick={handlePinBaseline}
                  disabled={pinning}
                  className="px-4 py-1.5 bg-electric-blue hover:bg-blue-600 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                >
                  {pinning ? 'Pinning...' : 'Confirm Baseline Pin'}
                </button>
              </div>
            )}

            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 text-slate-400">
                <RefreshCw className="w-8 h-8 animate-spin text-electric-blue mb-3" />
                <p className="text-sm font-medium text-slate-200">
                  Computing regression fingerprints and coverage diff...
                </p>
              </div>
            ) : error ? (
              <div className="p-6 bg-red-950/20 border border-red-800/40 rounded-xl text-center">
                <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-red-200">{error}</p>
                <p className="text-xs text-slate-400 mt-1">
                  Ensure at least two completed scans exist in this project to compute regressions.
                </p>
              </div>
            ) : report ? (
              <>
                {/* KPI Summary Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      Net Delta
                    </span>
                    <div className="flex items-center gap-1.5">
                      {report.summary.net_change > 0 ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-red-400" />
                          <span className="text-xl font-bold text-red-400">
                            +{report.summary.net_change}
                          </span>
                        </>
                      ) : report.summary.net_change < 0 ? (
                        <>
                          <TrendingDown className="w-4 h-4 text-emerald-400" />
                          <span className="text-xl font-bold text-emerald-400">
                            {report.summary.net_change}
                          </span>
                        </>
                      ) : (
                        <span className="text-xl font-bold text-slate-300">0</span>
                      )}
                    </div>
                  </div>

                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      New Regressions
                    </span>
                    <span className="text-xl font-bold text-red-400">
                      {report.summary.new_count}
                    </span>
                  </div>

                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      Resolved Issues
                    </span>
                    <span className="text-xl font-bold text-emerald-400">
                      {report.summary.resolved_count}
                    </span>
                  </div>

                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      Persistent
                    </span>
                    <span className="text-xl font-bold text-slate-200">
                      {report.summary.persistent_count}
                    </span>
                  </div>

                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      Changed
                    </span>
                    <span className="text-xl font-bold text-indigo-400">
                      {report.summary.changed_count}
                    </span>
                  </div>

                  <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                    <span className="text-[11px] font-medium text-slate-400 block mb-1">
                      Inconclusive
                    </span>
                    <span className="text-xl font-bold text-amber-400">
                      {report.summary.inconclusive_count}
                    </span>
                  </div>
                </div>

                {/* Coverage Warning / Confirmation */}
                <div
                  className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                    report.coverage.coverage_status === 'full'
                      ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                      : 'bg-amber-950/20 border-amber-800/40 text-amber-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {report.coverage.coverage_status === 'full' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    )}
                    <span>
                      {report.coverage.coverage_status === 'full'
                        ? `Full surface match: All ${report.coverage.matched_pages_count} pages match baseline coverage.`
                        : `Partial coverage: ${report.coverage.missing_pages_count} baseline page(s) missing from current scan.`}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Baseline: {new Date(report.baseline_scan_date).toLocaleDateString()} • Current:{' '}
                    {new Date(report.current_scan_date).toLocaleDateString()}
                  </span>
                </div>

                {/* Filter Tabs */}
                <div className="flex flex-wrap border-b border-slate-800 gap-2">
                  {(
                    ['all', 'new', 'resolved', 'persistent', 'changed', 'inconclusive'] as const
                  ).map((cls) => (
                    <button
                      key={cls}
                      type="button"
                      onClick={() => setFilterClass(cls)}
                      className={`pb-2 px-3 text-xs font-semibold border-b-2 capitalize transition-colors ${
                        filterClass === cls
                          ? 'border-electric-blue text-electric-blue'
                          : 'border-transparent text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {cls === 'all'
                        ? `All (${report.findings.length})`
                        : `${cls} (${
                            report.findings.filter((f) => f.classification === cls).length
                          })`}
                    </button>
                  ))}
                </div>

                {/* Findings Table */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden max-h-[420px] overflow-y-auto">
                  {filteredFindings.length > 0 ? (
                    <div className="divide-y divide-slate-800">
                      {filteredFindings.map((f) => {
                        const isNew = f.classification === 'new';
                        const isResolved = f.classification === 'resolved';
                        const isChanged = f.classification === 'changed';
                        const isInconclusive = f.classification === 'inconclusive';

                        return (
                          <div key={f.fingerprint} className="p-3.5 space-y-1.5 hover:bg-slate-800/30">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                                    isNew
                                      ? 'bg-red-950/80 text-red-300 border border-red-800/60'
                                      : isResolved
                                      ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                                      : isChanged
                                      ? 'bg-indigo-950/80 text-indigo-300 border border-indigo-800/60'
                                      : isInconclusive
                                      ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                                      : 'bg-slate-800 text-slate-300 border border-slate-700'
                                  }`}
                                >
                                  {f.classification}
                                </span>

                                <Badge
                                  variant={
                                    f.impact === 'critical'
                                      ? 'critical'
                                      : f.impact === 'serious'
                                      ? 'serious'
                                      : f.impact === 'minor'
                                      ? 'minor'
                                      : 'moderate'
                                  }
                                >
                                  {f.impact || 'moderate'}
                                </Badge>

                                <span className="font-semibold text-xs text-slate-200">
                                  {f.axe_rule_id}
                                </span>
                              </div>

                              <span className="text-[10px] text-slate-400 font-mono truncate max-w-xs">
                                {f.page_url}
                              </span>
                            </div>

                            <p className="text-xs text-slate-300">{f.description}</p>

                            {f.change_details && (
                              <p className="text-[11px] text-slate-400 italic">
                                Note: {f.change_details}
                              </p>
                            )}

                            {f.selector && (
                              <div className="font-mono text-[10px] text-slate-400 bg-slate-950/40 p-1.5 rounded border border-slate-800/60 break-all select-all">
                                {f.selector}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="p-8 text-center text-slate-400 text-xs">
                      No findings in classification category "{filterClass}".
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* Tab 2: Scheduled Recurring Audits */}
        {activeTab === 'schedules' && (
          <div className="space-y-5">
            {/* Create Schedule Form */}
            <form
              onSubmit={handleCreateSchedule}
              className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3"
            >
              <span className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
                <Plus className="w-4 h-4 text-electric-blue" />
                Schedule Automated Recurring Accessibility Audit
              </span>

              {scheduleError && (
                <div className="p-2.5 bg-red-950/30 border border-red-800/40 rounded-lg text-xs text-red-300 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                  {scheduleError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2">
                  <label htmlFor="schedule-target-url" className="text-[11px] text-slate-400 block mb-1">
                    Target Audit URL:
                  </label>
                  <input
                    id="schedule-target-url"
                    type="url"
                    required
                    value={newTargetUrl}
                    onChange={(e) => setNewTargetUrl(e.target.value)}
                    className="w-full bg-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:border-electric-blue"
                  />
                </div>

                <div>
                  <label htmlFor="schedule-cadence" className="text-[11px] text-slate-400 block mb-1">
                    Cadence:
                  </label>
                  <select
                    id="schedule-cadence"
                    value={newCadence}
                    onChange={(e) => setNewCadence(e.target.value)}
                    className="w-full bg-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:border-electric-blue"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly (Recommended)</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  Domain ownership must be verified prior to scheduled background auditing.
                </span>
                <button
                  type="submit"
                  className="px-4 py-2 bg-electric-blue hover:bg-blue-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Create Schedule
                </button>
              </div>
            </form>

            {/* Existing Schedules List */}
            <div className="space-y-3">
              <span className="text-xs font-semibold text-slate-300 block">
                Configured Audit Schedules ({schedules.length})
              </span>

              {schedulesLoading ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  Loading schedules...
                </div>
              ) : schedules.length > 0 ? (
                <div className="space-y-2">
                  {schedules.map((s) => (
                    <div
                      key={s.id}
                      className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              s.is_active
                                ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40'
                                : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}
                          >
                            {s.is_active ? 'Active' : 'Paused'}
                          </span>
                          <span className="font-semibold text-slate-200 capitalize">
                            {s.cadence} Audit
                          </span>
                        </div>
                        <p className="font-mono text-slate-400 text-[11px]">{s.target_url}</p>
                        <p className="text-[10px] text-slate-500">
                          Next Run: {s.next_run_at ? new Date(s.next_run_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleToggleSchedule(s.id, s.is_active)}
                          title={s.is_active ? 'Pause Schedule' : 'Resume Schedule'}
                          className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                        >
                          {s.is_active ? (
                            <Pause className="w-3.5 h-3.5" />
                          ) : (
                            <Play className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteSchedule(s.id)}
                          title="Delete Schedule"
                          className="p-2 bg-red-950/30 hover:bg-red-900/40 text-red-300 rounded-lg border border-red-800/40 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-900/30 border border-slate-800 rounded-xl text-slate-400 text-xs">
                  No automated audit schedules configured for this project yet.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
};
