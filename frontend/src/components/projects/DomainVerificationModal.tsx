import { useState } from "react";
import { Check, CheckCircle2, Clock, Copy, RefreshCw, ShieldAlert, ShieldCheck } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import {
  checkVerificationApi,
  Project,
  refreshVerificationApi,
  VerificationCheckResponse,
} from "../../api/projects";

export interface DomainVerificationModalProps {
  project: Project | null;
  isOpen: boolean;
  onClose: () => void;
  onProjectUpdated: (updatedProject: Project) => void;
}

export function DomainVerificationModal({
  project,
  isOpen,
  onClose,
  onProjectUpdated,
}: DomainVerificationModalProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [checkResult, setCheckResult] = useState<VerificationCheckResponse | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!project) return null;

  const verification = project.latest_verification;
  const isVerified = project.is_verified || verification?.status === "verified";

  const handleCopy = (field: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleVerifyNow = async () => {
    setIsChecking(true);
    setActionError(null);
    setCheckResult(null);
    try {
      const result = await checkVerificationApi(project.id);
      setCheckResult(result);
      if (result.verified) {
        onProjectUpdated({
          ...project,
          is_verified: true,
          latest_verification: result.verification,
        });
      }
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
        setActionError("Verification check failed. Please ensure the DNS TXT record is propagated.");
      }
    } finally {
      setIsChecking(false);
    }
  };

  const handleRefreshToken = async () => {
    setIsRefreshing(true);
    setActionError(null);
    try {
      const newVerification = await refreshVerificationApi(project.id);
      onProjectUpdated({
        ...project,
        is_verified: false,
        latest_verification: newVerification,
      });
      setCheckResult(null);
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
        setActionError("Failed to refresh verification token.");
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Domain Verification: ${project.base_domain}`}
      description="Ownership verification ensures scans only target web infrastructure you control."
      className="max-w-xl"
    >
      <div className="space-y-5 pt-2">
        {/* Status Banner */}
        <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2.5">
            {isVerified ? (
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
            ) : (
              <Clock className="h-5 w-5 text-amber-600" />
            )}
            <div>
              <p className="text-xs font-semibold text-slate-800">
                {isVerified ? "Ownership Verified" : "Verification Pending"}
              </p>
              <p className="text-[11px] text-slate-500">
                {isVerified
                  ? "This domain is authorized for automated crawling and accessibility audits."
                  : "Add the DNS TXT record below to your DNS management console."}
              </p>
            </div>
          </div>
          <Badge variant={isVerified ? "success" : "warning"}>
            {isVerified ? "Verified" : "Pending DNS"}
          </Badge>
        </div>

        {actionError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
          >
            <ShieldAlert className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
            <span>{actionError}</span>
          </div>
        )}

        {checkResult && (
          <div
            role="status"
            className={`flex items-start gap-2.5 rounded-lg border p-3 text-xs ${
              checkResult.verified
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-amber-200 bg-amber-50 text-amber-800"
            }`}
          >
            {checkResult.verified ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
            ) : (
              <Clock className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
            )}
            <span>{checkResult.message}</span>
          </div>
        )}

        {/* DNS Configuration Instructions */}
        {verification && (
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              DNS TXT Record Details
            </h3>

            {/* Record Type */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="col-span-1 rounded-md border border-slate-200 bg-slate-50 p-2.5">
                <span className="block text-slate-400 font-medium mb-0.5">Record Type</span>
                <span className="font-mono font-semibold text-slate-800">
                  {verification.record_type || "TXT"}
                </span>
              </div>
              <div className="col-span-2 rounded-md border border-slate-200 bg-slate-50 p-2.5">
                <span className="block text-slate-400 font-medium mb-0.5">Target Host / Name</span>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[11px] text-slate-800 break-all select-all">
                    {verification.record_name}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy("name", verification.record_name)}
                    className="p-1 text-slate-400 hover:text-slate-700"
                    title="Copy record host"
                    aria-label="Copy record host"
                  >
                    {copiedField === "name" ? (
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Record Value */}
            <div className="rounded-md border border-slate-200 bg-slate-50 p-2.5 text-xs">
              <span className="block text-slate-400 font-medium mb-0.5">Expected TXT Value</span>
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] text-slate-800 break-all select-all">
                  {verification.expected_value}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy("value", verification.expected_value)}
                  className="p-1 text-slate-400 hover:text-slate-700"
                  title="Copy expected value"
                  aria-label="Copy expected value"
                >
                  {copiedField === "value" ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
          <Button
            type="button"
            variant="ghost"
            onClick={handleRefreshToken}
            disabled={isRefreshing || isChecking}
            className="text-xs text-slate-500 hover:text-slate-700 gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Regenerate Challenge
          </Button>

          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Close
            </Button>
            {!isVerified && (
              <Button
                type="button"
                onClick={handleVerifyNow}
                disabled={isChecking || isRefreshing}
                className="gap-1.5"
              >
                <CheckCircle2 className={`h-4 w-4 ${isChecking ? "animate-spin" : ""}`} />
                {isChecking ? "Checking DNS..." : "Verify DNS Now"}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Dialog>
  );
}
