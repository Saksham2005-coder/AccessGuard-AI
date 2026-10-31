import { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Ban,
  CheckCircle2,
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
        setActionError("Failed to cancel scan execution.");
      }
    } finally {
      setIsCancelling(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Audit Execution Telemetry"
      description={`Real-time Playwright execution logs and axe-core audit results for ${scan?.target_url || ""}`}
      className="max-w-2xl"
    >
      <div className="space-y-4 pt-2">
        {/* Error Alert */}
        {actionError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
          >
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{actionError}</span>
          </div>
        )}

        {/* Status & Engine Header */}
        <div className="flex items-center justify-between p-3.5 rounded-xl border border-[#303741] bg-[#171C23]">
          <div className="flex items-center gap-2.5">
            {isActive ? (
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#38BDF8] opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-[#38BDF8]" />
              </span>
            ) : isCompleted ? (
              <CheckCircle2 className="h-5 w-5 text-[#34D399]" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-[#FB7185]" />
            )}
            <div>
              <span className="text-xs font-semibold text-[#F3F4F6] capitalize">
                Status: {scan?.status || "Loading..."}
              </span>
              <div className="text-[11px] text-[#9CA3AF]">
                axe-core {scan?.axe_version || "4.14.0"} • {scan?.browser_version || "Chromium"}
              </div>
            </div>
          </div>

          <Badge
            variant={isCompleted ? "success" : isFailed ? "critical" : "primary"}
            className="capitalize"
          >
            {scan?.status || "pending"}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5 rounded-xl border border-[#303741] bg-[#171C23] p-4">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#9CA3AF] uppercase tracking-wider text-[11px]">Crawl Progress</span>
            <span className="text-[#38BDF8] font-mono">{progressPercent}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[#111315] border border-[#303741]">
            <div
              className="h-full bg-gradient-to-r from-[#38BDF8] to-[#0EA5E9] transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-[#9CA3AF] pt-1">
            <span>Pages: {processedPages} of {maxPages} max</span>
            <span>Violations: <strong className="text-[#FB7185] font-mono">{scan?.total_violations || 0}</strong></span>
          </div>
        </div>

        {/* Telemetry Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3 text-center">
            <div className="text-[#9CA3AF] text-[11px]">Pages Crawled</div>
            <div className="text-lg font-bold font-mono text-[#34D399] mt-0.5">
              {scan?.pages_succeeded || 0}
            </div>
          </div>
          <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3 text-center">
            <div className="text-[#9CA3AF] text-[11px]">axe-core Version</div>
            <div className="text-lg font-bold font-mono text-[#F3F4F6] mt-0.5">
              {scan?.axe_version || "4.14.0"}
            </div>
          </div>
          <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3 text-center">
            <div className="text-[#9CA3AF] text-[11px]">Max Depth</div>
            <div className="text-lg font-bold font-mono text-[#F3F4F6] mt-0.5">
              {String(scan?.config?.max_depth ?? 2)}
            </div>
          </div>
          <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3 text-center">
            <div className="text-[#9CA3AF] text-[11px]">Violations Found</div>
            <div className="text-lg font-bold font-mono text-[#FB7185] mt-0.5">
              {scan?.total_violations || 0}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-[#303741]">
          {isActive ? (
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              isLoading={isCancelling}
              className="text-xs gap-1.5"
            >
              <Ban className="h-3.5 w-3.5" />
              <span>Cancel Scan</span>
            </Button>
          ) : (
            <div className="text-xs text-[#9CA3AF] font-mono">
              Completed at: {scan?.completed_at ? new Date(scan.completed_at).toLocaleTimeString() : "N/A"}
            </div>
          )}

          <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
            Close
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
