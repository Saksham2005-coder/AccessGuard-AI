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
      description="To prevent unauthorized scanning and SSRF abuse, domain ownership must be proven via DNS TXT record."
      className="max-w-xl"
    >
      <div className="space-y-4 pt-2">
        {/* Verification Status Header Banner */}
        <div className="flex items-center justify-between p-3.5 rounded-xl border border-[#303741] bg-[#171C23]">
          <div className="flex items-center gap-2.5">
            {isVerified ? (
              <ShieldCheck className="h-5 w-5 text-[#34D399]" />
            ) : (
              <Clock className="h-5 w-5 text-[#FBBF24]" />
            )}
            <div>
              <div className="text-xs font-semibold text-[#F3F4F6]">
                {isVerified ? "Domain Ownership Verified" : "Awaiting DNS Propagation"}
              </div>
              <div className="text-[11px] text-[#9CA3AF]">
                {isVerified
                  ? `Verified at ${new Date(verification?.verified_at || project.updated_at).toLocaleDateString()}`
                  : "Create the DNS TXT record below to authorize scans"}
              </div>
            </div>
          </div>
          <Badge variant={isVerified ? "success" : "warning"} className="capitalize">
            {verification?.status || "pending"}
          </Badge>
        </div>

        {/* Error or Alert Message */}
        {actionError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
          >
            <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{actionError}</span>
          </div>
        )}

        {/* Verification Success Feedback */}
        {checkResult && checkResult.verified && (
          <div className="flex items-start gap-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-[#34D399]">
            <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{checkResult.message || "Domain verified successfully! You may now launch accessibility scans."}</span>
          </div>
        )}

        {/* DNS Challenge Instructions */}
        {verification && (
          <div className="space-y-3 rounded-xl border border-[#303741] bg-[#171C23] p-4 text-xs">
            <h4 className="font-semibold text-[#F3F4F6] text-xs uppercase tracking-wider">
              Required DNS TXT Record
            </h4>

            {/* Record Type */}
            <div>
              <span className="text-[11px] font-medium text-[#9CA3AF]">Record Type:</span>
              <div className="mt-1 font-mono font-semibold text-[#38BDF8] bg-[#111315] border border-[#303741] px-2.5 py-1.5 rounded-lg">
                TXT
              </div>
            </div>

            {/* Host / Name */}
            <div>
              <div className="flex items-center justify-between text-[11px] text-[#9CA3AF]">
                <span>Host / Name:</span>
                <button
                  type="button"
                  onClick={() => handleCopy("name", verification.record_name)}
                  className="text-[#38BDF8] hover:text-[#0EA5E9] inline-flex items-center gap-1 font-medium transition-colors"
                >
                  {copiedField === "name" ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  <span>{copiedField === "name" ? "Copied" : "Copy Name"}</span>
                </button>
              </div>
              <div className="mt-1 font-mono text-xs text-[#F3F4F6] bg-[#111315] border border-[#303741] px-2.5 py-1.5 rounded-lg break-all">
                {verification.record_name}
              </div>
            </div>

            {/* Value / Content */}
            <div>
              <div className="flex items-center justify-between text-[11px] text-[#9CA3AF]">
                <span>Value / Content:</span>
                <button
                  type="button"
                  onClick={() => handleCopy("val", verification.expected_value)}
                  className="text-[#38BDF8] hover:text-[#0EA5E9] inline-flex items-center gap-1 font-medium transition-colors"
                  aria-label="Copy DNS Token"
                >
                  {copiedField === "val" ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  <span>{copiedField === "val" ? "Copied Token" : "Copy DNS Token"}</span>
                </button>
              </div>
              <div className="mt-1 font-mono text-xs text-[#F3F4F6] bg-[#111315] border border-[#303741] px-2.5 py-1.5 rounded-lg break-all">
                {verification.expected_value}
              </div>
            </div>

            <div className="text-[11px] text-[#6B7280] pt-1">
              DNS propagation typically takes 1 to 5 minutes depending on your DNS host TTL settings.
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-3 border-t border-[#303741]">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRefreshToken}
            isLoading={isRefreshing}
            disabled={isVerified}
            className="text-xs gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Generate New Token</span>
          </Button>

          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
              Close
            </Button>
            {!isVerified && (
              <Button
                type="button"
                size="sm"
                onClick={handleVerifyNow}
                isLoading={isChecking}
                className="text-xs gap-1.5 font-semibold"
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Verify DNS Now</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </Dialog>
  );
}
