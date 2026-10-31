import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  ExternalLink,
  Shield,
} from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { cancelScanApi, getScanApi, Scan } from "../../api/scans";

export interface ScanDetailModalProps {
  scanId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onScanUpdated?: (scan: Scan) => void;
}

export function ScanDetailModal({
  scanId,
  isOpen,
  onClose,
  onScanUpdated,
}: ScanDetailModalProps) {
  const [scan, setScan] = useState<Scan | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const isLoading = !scan || scan.id !== scanId;

  // Poll for scan status while active
  useEffect(() => {
    if (!isOpen || !scanId) return;

    let isMounted = true;

    const fetchScan = async () => {
      try {
        const data = await getScanApi(scanId);
        if (isMounted) {
          setScan(data);
          onScanUpdated?.(data);
        }
      } catch (err) {
        console.error("Failed to refresh scan details", err);
      }
    };

    fetchScan();

    const interval = setInterval(() => {
      if (
        scan?.status === "pending" ||
        scan?.status === "running" ||
        scan?.status === "crawling" ||
        scan?.status === "auditing"
      ) {
        fetchScan();
      }
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [isOpen, scanId, scan?.status, onScanUpdated]);

  if (!isOpen || !scanId) return null;

  const isActive =
    scan?.status === "pending" ||
    scan?.status === "running" ||
    scan?.status === "crawling" ||
    scan?.status === "auditing";

  const isCompleted =
    scan?.status === "completed" || scan?.status === "completed_with_errors";

  const isFailed = scan?.status === "failed" || scan?.status === "cancelled";

  const maxPages = scan?.config?.max_pages ? Number(scan.config.max_pages) : 20;
  const processedPages = (scan?.pages_succeeded || 0) + (scan?.pages_failed || 0);
  const progressPercent = Math.min(
    100,
    Math.round((processedPages / (maxPages || 1)) * 100)
  );

  const handleCancel = async () => {
    if (!scan) return;
    setIsCancelling(true);
    setActionError(null);
    try {
      await cancelScanApi(scan.id);
      const updated = await getScanApi(scan.id);
      setScan(updated);
      onScanUpdated?.(updated);
    } catch (err: unknown) {
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "detail" in err.response.data &&
        typeof err.response.data.detail === "string"
      ) {
        setActionError(err.response.data.detail);
      } else {
        setActionError("Failed to cancel scan.");
      }
    } finally {
      setIsCancelling(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Accessibility Scan Execution"
      description="Multi-page Playwright crawling and axe-core accessibility audit status."
      className="max-w-xl"
    >
      <div className="space-y-5 pt-2">
        {isLoading && !scan ? (
          <div className="py-8 text-center text-sm text-slate-500">
            Loading scan telemetry...
          </div>
        ) : scan ? (
          <>
            {/* Target URL Header */}
            <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-slate-50">
              <div className="space-y-0.5 max-w-[70%]">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Target Endpoint
                </span>
                <a
                  href={scan.target_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs font-mono font-medium text-[#4657D8] hover:underline truncate"
                >
                  <span className="truncate">{scan.target_url}</span>
                  <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                </a>
              </div>
              <Badge
                variant={
                  isActive
                    ? "default"
                    : isCompleted
                      ? "success"
                      : "critical"
                }
                className="capitalize shrink-0 gap-1.5"
              >
                {isActive && <Activity className="h-3 w-3 animate-spin" />}
                {isCompleted && <CheckCircle2 className="h-3 w-3" />}
                {isFailed && <AlertCircle className="h-3 w-3" />}
                <span>{scan.status.replace("_", " ")}</span>
              </Badge>
            </div>

            {actionError && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
              >
                <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
                <span>{actionError}</span>
              </div>
            )}

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Crawl Progress</span>
                <span>{isActive ? `${progressPercent}%` : isCompleted ? "100%" : "Terminated"}</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    isActive
                      ? "bg-[#4657D8] animate-pulse"
                      : isCompleted
                        ? "bg-emerald-600"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${isCompleted ? 100 : progressPercent}%` }}
                />
              </div>
            </div>

            {/* Telemetry Metrics Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-lg border border-slate-200 bg-white text-center">
                <div className="text-xl font-bold text-slate-900">
                  {processedPages}
                  <span className="text-xs font-normal text-slate-400">/{maxPages}</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Pages Crawled</p>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white text-center">
                <div
                  className={`text-xl font-bold ${
                    scan.total_violations > 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {scan.total_violations}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Violations Found</p>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white text-center">
                <div className="text-xl font-bold text-slate-900 font-mono text-sm pt-0.5">
                  {scan.axe_version || "4.14.0"}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">axe-core Version</p>
              </div>
            </div>

            {/* Error Summary if failed */}
            {scan.error_summary && (
              <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-xs text-red-800 space-y-1">
                <p className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span>Execution Notice</span>
                </p>
                <p className="font-mono text-[11px]">{scan.error_summary}</p>
              </div>
            )}

            {/* Audit Details */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 space-y-1">
              <div className="flex items-center gap-2 text-slate-700">
                <Shield className="h-4 w-4 text-[#4657D8]" />
                <span className="font-medium">Rule Engine: WCAG 2.1 & 2.2 Level A/AA</span>
              </div>
              <div className="flex items-center gap-2 text-slate-500">
                <Clock className="h-4 w-4" />
                <span>
                  Started: {scan.started_at ? new Date(scan.started_at).toLocaleTimeString() : "Pending start"}
                </span>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              {isActive ? (
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={handleCancel}
                  disabled={isCancelling}
                  className="gap-1.5 text-xs"
                >
                  <Ban className="h-3.5 w-3.5" />
                  <span>{isCancelling ? "Cancelling..." : "Cancel Scan"}</span>
                </Button>
              ) : (
                <div />
              )}

              <Button type="button" variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          </>
        ) : null}
      </div>
    </Dialog>
  );
}
