import { useState, useEffect } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Code2,
  Columns,
  FileCheck2,
  RotateCw,
  Shield,
  SlidersHorizontal,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import {
  ComparisonResponse,
  getRemediationComparisonApi,
  runRemediationComparisonApi,
} from "../../api/remediations";

export interface LiveComparisonModalProps {
  remediationId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove?: (remediationId: string) => void;
  onReject?: (remediationId: string) => void;
  isPendingApproval?: boolean;
}

export function LiveComparisonModal({
  remediationId,
  isOpen,
  onClose,
  onApprove,
  onReject,
  isPendingApproval = false,
}: LiveComparisonModalProps) {
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"split" | "wipe" | "diff" | "audit">("split");
  const [wipePercent, setWipePercent] = useState<number>(50);

  useEffect(() => {
    if (!isOpen || !remediationId) return;

    let isMounted = true;
    const fetchComparison = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await getRemediationComparisonApi(remediationId);
        if (isMounted) setData(res);
      } catch (err) {
        console.error("Failed to load comparison data", err);
        if (isMounted) setError("Failed to load comparison preview.");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchComparison();

    return () => {
      isMounted = false;
    };
  }, [isOpen, remediationId]);

  const handleRefreshComparison = async () => {
    if (!remediationId) return;
    setIsRefreshing(true);
    setError(null);
    try {
      const res = await runRemediationComparisonApi(remediationId);
      setData(res);
    } catch (err) {
      console.error("Failed to re-run comparison", err);
      setError("Failed to re-generate comparison.");
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!isOpen || !remediationId) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Live Isolated Before-and-After Comparison"
      description="Interactive side-by-side visual difference, DOM structure patch, and axe-core re-audit in an isolated headless Chromium sandbox."
      className="max-w-5xl"
    >
      <div className="space-y-4 pt-2">
        {/* Isolated Sandbox Policy Banner */}
        <div className="flex items-start gap-2.5 rounded-xl border border-[#38BDF8]/20 bg-[#38BDF8]/5 p-3 text-xs text-[#38BDF8]">
          <Shield className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            <strong>Isolated Sandbox Simulation:</strong> Live production websites are never modified.
            All patches are tested inside a contained browser session with external network egress aborted.
          </span>
        </div>

        {/* Navigation & View Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-[#303741] bg-[#171C23]">
          <div className="flex items-center gap-1.5 rounded-lg border border-[#303741] bg-[#111315] p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setViewMode("split")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                viewMode === "split"
                  ? "bg-[#252C35] text-[#38BDF8] font-semibold"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
            >
              <Columns className="h-3.5 w-3.5" />
              <span>Side-by-Side</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("wipe")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                viewMode === "wipe"
                  ? "bg-[#252C35] text-[#38BDF8] font-semibold"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>Wipe Slider</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("diff")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                viewMode === "diff"
                  ? "bg-[#252C35] text-[#38BDF8] font-semibold"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
            >
              <Code2 className="h-3.5 w-3.5" />
              <span>DOM Diff</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("audit")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                viewMode === "audit"
                  ? "bg-[#252C35] text-[#38BDF8] font-semibold"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
            >
              <FileCheck2 className="h-3.5 w-3.5" />
              <span>Re-Audit Details</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleRefreshComparison}
              isLoading={isRefreshing}
              className="text-xs gap-1.5 h-8"
              title="Re-run isolated headless validation"
            >
              <RotateCw className="h-3.5 w-3.5" />
              <span>Re-Audit Patch</span>
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
          >
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Re-Audit Status Bar */}
        {data && (
          <div
            className={`p-3 rounded-xl border text-xs flex flex-wrap items-center justify-between gap-2 ${
              data.passed
                ? "border-emerald-500/30 bg-emerald-500/10 text-[#34D399]"
                : "border-rose-500/30 bg-rose-500/10 text-[#FB7185]"
            }`}
          >
            <div className="flex items-center gap-2 font-medium">
              {data.passed ? (
                <CheckCircle2 className="h-4 w-4 text-[#34D399] shrink-0" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-[#FB7185] shrink-0" />
              )}
              <span>
                Isolated axe-core Re-Audit:{" "}
                <strong>
                  {data.passed
                    ? `Resolved '${data.rule_id}' with zero new regressions`
                    : `Resolution Incomplete or Flagged New Regressions`}
                </strong>
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-[#9CA3AF]">
              <span>axe-core {String(data.details?.axe_version || "4.14.0")}</span>
              <span>•</span>
              <span>Duration: {String(data.details?.duration_ms || 0)}ms</span>
            </div>
          </div>
        )}

        {/* Content Body */}
        {isLoading ? (
          <div className="flex h-80 items-center justify-center rounded-xl border border-[#303741] bg-[#171C23]">
            <div className="flex flex-col items-center gap-3">
              <div className="h-7 w-7 animate-spin rounded-full border-2 border-[#38BDF8] border-t-transparent" />
              <p className="text-xs text-[#9CA3AF]">Generating isolated before-and-after comparison...</p>
            </div>
          </div>
        ) : !data ? (
          <div className="flex h-64 items-center justify-center rounded-xl border border-[#303741] bg-[#171C23] text-center p-6">
            <p className="text-xs text-[#9CA3AF]">No comparison data available.</p>
          </div>
        ) : viewMode === "split" ? (
          /* Side-by-Side View */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: Original Snapshot */}
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2.5 rounded-lg border border-[#303741] bg-[#171C23]">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[#FB7185]" />
                  <span className="text-xs font-semibold text-[#FB7185]">
                    Original Snapshot (Violating)
                  </span>
                </div>
                <Badge variant="critical" className="text-[10px]">
                  Failing {data.rule_id}
                </Badge>
              </div>

              <div className="rounded-xl border border-[#303741] bg-[#111315] p-3 overflow-auto max-h-[460px] min-h-[260px] flex items-center justify-center">
                {data.before_screenshot_url ? (
                  <img
                    src={data.before_screenshot_url}
                    alt="Original isolated snapshot before remediation"
                    className="max-h-[440px] max-w-full rounded border border-[#303741] object-contain"
                  />
                ) : (
                  <div className="w-full">
                    <pre className="text-xs font-mono text-rose-300 whitespace-pre-wrap break-all p-3 bg-rose-950/20 rounded border border-rose-900/30">
                      {data.before_html}
                    </pre>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Proposed Patch */}
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2.5 rounded-lg border border-[#303741] bg-[#171C23]">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[#34D399]" />
                  <span className="text-xs font-semibold text-[#34D399]">
                    Proposed Patch (Compliant)
                  </span>
                </div>
                <Badge variant="success" className="text-[10px]">
                  Resolved
                </Badge>
              </div>

              <div className="rounded-xl border border-[#303741] bg-[#111315] p-3 overflow-auto max-h-[460px] min-h-[260px] flex items-center justify-center">
                {data.after_screenshot_url ? (
                  <img
                    src={data.after_screenshot_url}
                    alt="Proposed isolated snapshot after remediation patch"
                    className="max-h-[440px] max-w-full rounded border border-[#303741] object-contain"
                  />
                ) : (
                  <div className="w-full">
                    <pre className="text-xs font-mono text-emerald-300 whitespace-pre-wrap break-all p-3 bg-emerald-950/20 rounded border border-emerald-900/30">
                      {data.after_html}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : viewMode === "wipe" ? (
          /* Wipe Slider Mode */
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-[#9CA3AF] px-1">
              <span>Original (0%)</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[#38BDF8]">{wipePercent}% Split</span>
                <button
                  type="button"
                  onClick={() => setWipePercent(0)}
                  className="px-2 py-0.5 rounded border border-[#303741] hover:border-[#38BDF8]"
                >
                  Original Only
                </button>
                <button
                  type="button"
                  onClick={() => setWipePercent(50)}
                  className="px-2 py-0.5 rounded border border-[#303741] hover:border-[#38BDF8]"
                >
                  50 / 50
                </button>
                <button
                  type="button"
                  onClick={() => setWipePercent(100)}
                  className="px-2 py-0.5 rounded border border-[#303741] hover:border-[#38BDF8]"
                >
                  Patched Only
                </button>
              </div>
              <span>Proposed (100%)</span>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              value={wipePercent}
              onChange={(e) => setWipePercent(Number(e.target.value))}
              aria-label="Wipe comparison slider between original and patched snapshots"
              className="w-full accent-[#38BDF8] cursor-pointer"
            />

            <div className="relative rounded-xl border border-[#303741] bg-[#111315] overflow-hidden h-[420px] flex items-center justify-center">
              {data.after_screenshot_url && data.before_screenshot_url ? (
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* Underneath: After screenshot */}
                  <img
                    src={data.after_screenshot_url}
                    alt="Proposed snapshot"
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                  />

                  {/* Overneath: Before screenshot with clip-path */}
                  <div
                    className="absolute inset-0 overflow-hidden"
                    style={{ width: `${wipePercent}%` }}
                  >
                    <img
                      src={data.before_screenshot_url}
                      alt="Original snapshot"
                      className="absolute inset-0 w-full h-full object-contain pointer-events-none max-w-none"
                    />
                  </div>

                  {/* Divider Line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-[#38BDF8] shadow-[0_0_8px_#38BDF8]"
                    style={{ left: `${wipePercent}%` }}
                  />
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-[#9CA3AF]">
                  <p>Screenshots unavailable for visual wipe slider.</p>
                  <p className="mt-1">Please use the DOM Diff or Side-by-Side code view.</p>
                </div>
              )}
            </div>
          </div>
        ) : viewMode === "diff" ? (
          /* DOM Unified Diff */
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2.5 rounded-lg border border-[#303741] bg-[#171C23] text-xs">
              <span className="font-semibold text-[#F3F4F6] font-mono">
                Unified Diff: Original vs. Patched DOM
              </span>
              <span className="text-[#9CA3AF] text-[11px]">
                {data.patch_operations.length} allowlisted operation(s) applied
              </span>
            </div>

            <pre className="p-4 rounded-xl border border-[#303741] bg-[#111315] text-xs font-mono text-[#D1D5DB] overflow-x-auto max-h-[460px] whitespace-pre-wrap select-all">
              {data.dom_diff || "No textual DOM differences detected."}
            </pre>
          </div>
        ) : (
          /* Re-Audit Details */
          <div className="space-y-3">
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-4 space-y-3 text-xs">
              <h4 className="font-semibold text-[#F3F4F6] uppercase tracking-wider text-[11px]">
                Audit Findings Before & After
              </h4>

              <div className="space-y-2">
                <div className="flex items-center justify-between p-2.5 rounded-lg border border-[#303741] bg-[#111315]">
                  <div>
                    <span className="font-mono font-bold text-[#F3F4F6]">{data.rule_id}</span>
                    <p className="text-[11px] text-[#9CA3AF] mt-0.5">Original target accessibility barrier</p>
                  </div>
                  <Badge variant={data.original_rule_resolved ? "success" : "critical"}>
                    {data.original_rule_resolved ? "Resolved" : "Still Failing"}
                  </Badge>
                </div>

                {data.new_violations.length > 0 ? (
                  data.new_violations.map((nv, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-xs text-[#FB7185]"
                    >
                      <div>
                        <span className="font-mono font-bold">{nv.rule_id}</span>
                        <p className="text-[11px] text-rose-300 mt-0.5">{nv.description}</p>
                      </div>
                      <Badge variant="critical">Regression ({nv.impact})</Badge>
                    </div>
                  ))
                ) : (
                  <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 text-xs text-[#34D399] flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Zero new accessibility regressions detected in isolated re-audit.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-[#303741]">
          <div className="text-[11px] text-[#9CA3AF] font-mono">
            Remediation: {remediationId.slice(0, 8)}...
          </div>

          <div className="flex items-center gap-2">
            {isPendingApproval && (
              <>
                {onReject && (
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      onReject(remediationId);
                      onClose();
                    }}
                    className="text-xs gap-1.5"
                  >
                    <ThumbsDown className="h-3.5 w-3.5" />
                    <span>Reject</span>
                  </Button>
                )}
                {onApprove && (
                  <Button
                    type="button"
                    variant="default"
                    size="sm"
                    onClick={() => {
                      onApprove(remediationId);
                      onClose();
                    }}
                    className="text-xs gap-1.5 font-semibold"
                  >
                    <ThumbsUp className="h-3.5 w-3.5" />
                    <span>Approve Patch</span>
                  </Button>
                )}
              </>
            )}

            <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
              Close
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
