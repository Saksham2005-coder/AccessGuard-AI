import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Code,
  FileCheck2,
  Play,
  Shield,
  SlidersHorizontal,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card, CardContent } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { Dialog } from "../components/ui/Dialog";
import {
  approveRemediationApi,
  listRemediationsApi,
  rejectRemediationApi,
  validateRemediationApi,
  Remediation,
} from "../api/remediations";
import { LiveComparisonModal } from "../components/remediations/LiveComparisonModal";

export function RemediationsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedRemediation, setSelectedRemediation] = useState<Remediation | null>(null);
  const [comparisonRemediationId, setComparisonRemediationId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | null>(null);
  const [comments, setComments] = useState<string>("");

  const {
    data: remediations = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["remediations", statusFilter],
    queryFn: () =>
      listRemediationsApi({
        status_filter: statusFilter || undefined,
      }),
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      approveRemediationApi(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["remediations"] });
      handleCloseModal();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      rejectRemediationApi(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["remediations"] });
      handleCloseModal();
    },
  });

  const validateMutation = useMutation({
    mutationFn: (id: string) => validateRemediationApi(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["remediations"] });
    },
  });

  const handleOpenAction = (remediation: Remediation, type: "approve" | "reject") => {
    setSelectedRemediation(remediation);
    setActionType(type);
    setComments("");
  };

  const handleCloseModal = () => {
    setSelectedRemediation(null);
    setActionType(null);
    setComments("");
  };

  const handleConfirmDecision = async () => {
    if (!selectedRemediation || !actionType) return;
    if (actionType === "approve") {
      await approveMutation.mutateAsync({
        id: selectedRemediation.id,
        notes: comments,
      });
    } else {
      await rejectMutation.mutateAsync({
        id: selectedRemediation.id,
        notes: comments,
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "validated":
        return (
          <Badge variant="success" className="gap-1.5 font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Validated</span>
          </Badge>
        );
      case "approved":
        return (
          <Badge variant="primary" className="gap-1.5 font-semibold">
            <ThumbsUp className="h-3.5 w-3.5" />
            <span>Approved</span>
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="critical" className="gap-1.5 font-semibold">
            <XCircle className="h-3.5 w-3.5" />
            <span>Rejected</span>
          </Badge>
        );
      case "validation_failed":
        return (
          <Badge variant="critical" className="gap-1.5 font-semibold">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Validation Failed</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="warning" className="gap-1.5 font-semibold">
            <Clock className="h-3.5 w-3.5" />
            <span>Pending Review</span>
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            AI Remediation Review
          </h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Evidence-grounded code proposals, human-in-the-loop review, and isolated snapshot validation.
          </p>
        </div>

        {/* Filter Dropdown */}
        <div className="flex items-center gap-2.5">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 rounded-lg border border-[#303741] bg-[#171C23] px-3 text-xs font-medium text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors cursor-pointer"
            aria-label="Filter remediations by status"
          >
            <option value="" className="bg-[#1D2229]">All Proposals</option>
            <option value="proposed" className="bg-[#1D2229]">Proposed (Pending Review)</option>
            <option value="approved" className="bg-[#1D2229]">Approved</option>
            <option value="validated" className="bg-[#1D2229]">Snapshot Validated</option>
            <option value="validation_failed" className="bg-[#1D2229]">Validation Failed</option>
            <option value="rejected" className="bg-[#1D2229]">Rejected</option>
          </select>
        </div>
      </div>

      {/* Observability Boundary Banner */}
      <div className="rounded-xl border border-[#303741] bg-[#171A1F] p-4 text-xs">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-[#38BDF8] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-[#F3F4F6] uppercase tracking-wider text-[11px]">
              Human-in-the-Loop Safe Patch Policy
            </span>
            <p className="text-[#9CA3AF] mt-0.5 leading-relaxed">
              AI remediations are immutable suggestions requiring engineer review. Once approved, the patch is reconstructed and re-tested in an isolated headless Chromium sandbox with network egress aborted before code incorporation.
            </p>
          </div>
        </div>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="space-y-4" aria-busy="true">
          {[1, 2].map((i) => (
            <Card key={i} className="p-6 space-y-4">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="h-4 w-2/3" />
              <div className="grid grid-cols-2 gap-4 pt-2">
                <Skeleton className="h-28 w-full" />
                <Skeleton className="h-28 w-full" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && remediations.length === 0 && (
        <EmptyState
          icon={Sparkles}
          title="No Remediation Proposals"
          description="Navigate to Findings and select 'Generate AI Remediation' on any detected accessibility barrier to initiate LangGraph analysis."
        />
      )}

      {/* Remediations List */}
      {!isLoading && !isError && remediations.length > 0 && (
        <div className="space-y-6">
          {remediations.map((r) => {
            const isPending = r.status === "pending_approval";
            const isApproved = r.status === "approved";
            const latestValidation = r.validation_results?.[r.validation_results.length - 1];

            return (
              <Card
                key={r.id}
                className="hover:border-[#38BDF8]/40 transition-all overflow-hidden"
              >
                <CardContent className="p-6 space-y-5">
                  {/* Top Bar: Root Cause & Status */}
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div className="space-y-1 max-w-2xl">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-[#38BDF8]">
                          Root Cause Analysis
                        </span>
                        <span>•</span>
                        <span className="text-xs text-[#9CA3AF] font-mono">
                          Format: {r.patch_format}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold text-[#F3F4F6] leading-snug">
                        {r.root_cause}
                      </h3>
                      <p className="text-xs text-[#9CA3AF] leading-relaxed">
                        {r.recommendation}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 shrink-0">
                      {getStatusBadge(r.status)}
                      {r.confidence && (
                        <Badge variant="outline" className="text-xs font-mono text-[#38BDF8] border-[#38BDF8]/30">
                          {Math.round(r.confidence * 100)}% Confidence
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Split-Panel Code Review Diff View */}
                  <div className="rounded-xl border border-[#303741] overflow-hidden bg-[#111315]">
                    <div className="bg-[#171A1F] px-4 py-2 border-b border-[#303741] flex items-center justify-between text-xs font-semibold text-[#9CA3AF]">
                      <div className="flex items-center gap-2">
                        <Code className="h-3.5 w-3.5 text-[#38BDF8]" />
                        <span className="text-[#F3F4F6]">DOM Patch Comparison</span>
                      </div>
                      <span className="text-[11px] font-mono text-[#6B7280]">
                        Model: {r.model_provider || "AI"} ({r.model_name || "llm"})
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#303741]">
                      {/* Left Side: Before Snippet (Original Violation) */}
                      <div className="p-4 bg-rose-950/10">
                        <div className="flex items-center justify-between pb-2 mb-2 border-b border-rose-900/30 text-xs">
                          <span className="font-semibold text-[#FB7185] flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-[#FB7185]" />
                            <span>Original Element (Violating)</span>
                          </span>
                        </div>
                        <pre className="text-xs font-mono text-rose-300 overflow-x-auto whitespace-pre-wrap break-all select-all">
                          {r.before_snippet || "No before snippet available"}
                        </pre>
                      </div>

                      {/* Right Side: After Snippet (Proposed Safe Fix) */}
                      <div className="p-4 bg-emerald-950/10">
                        <div className="flex items-center justify-between pb-2 mb-2 border-b border-emerald-900/30 text-xs">
                          <span className="font-semibold text-[#34D399] flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-[#34D399]" />
                            <span>Proposed Patch (Compliant)</span>
                          </span>
                        </div>
                        <pre className="text-xs font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap break-all select-all">
                          {r.after_snippet || "No after snippet provided"}
                        </pre>
                      </div>
                    </div>
                  </div>

                  {/* Validation Results Audit Banner */}
                  {latestValidation && (
                    <div
                      className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
                        latestValidation.passed
                          ? "border-emerald-500/30 bg-emerald-500/10 text-[#34D399]"
                          : "border-rose-500/30 bg-rose-500/10 text-[#FB7185]"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {latestValidation.passed ? (
                          <FileCheck2 className="h-4 w-4 text-[#34D399] shrink-0" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-[#FB7185] shrink-0" />
                        )}
                        <span>
                          Isolated snapshot test:{" "}
                          <strong>
                            {latestValidation.passed
                              ? "Clean Pass (Original rule resolved, zero regressions)"
                              : "Validation Flagged New Regressions"}
                          </strong>
                        </span>
                      </div>
                      <span className="text-[11px] text-[#9CA3AF] font-mono">
                        {new Date(latestValidation.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  )}

                  {/* Human Approvals Audit Log */}
                  {r.approvals && r.approvals.length > 0 && (
                    <div className="pt-2 text-xs text-[#9CA3AF] border-t border-[#303741] flex items-center justify-between">
                      <span>
                        Reviewed by tenant:{" "}
                        <strong className="capitalize text-[#F3F4F6]">
                          {r.approvals[r.approvals.length - 1].decision}
                        </strong>
                        {r.approvals[r.approvals.length - 1].comments && (
                          <span className="italic ml-2 text-[#9CA3AF]">
                            &ldquo;{r.approvals[r.approvals.length - 1].comments}&rdquo;
                          </span>
                        )}
                      </span>
                      <span className="font-mono text-[11px]">
                        {new Date(r.approvals[r.approvals.length - 1].created_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}

                  {/* Actions Bar */}
                  <div className="pt-3 border-t border-[#303741] flex items-center justify-between gap-3">
                    <div className="text-[11px] text-[#6B7280]">
                      Proposal ID: <span className="font-mono">{r.id.slice(0, 8)}...</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Compare button */}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setComparisonRemediationId(r.id)}
                        className="text-xs gap-1.5"
                        title="Compare original vs proposed snapshot in isolated sandbox"
                      >
                        <SlidersHorizontal className="h-3.5 w-3.5 text-[#38BDF8]" />
                        <span>Live Comparison</span>
                      </Button>

                      {/* If approved but not validated yet, allow triggering snapshot validation */}
                      {isApproved && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => validateMutation.mutate(r.id)}
                          isLoading={validateMutation.isPending}
                          className="text-xs gap-1.5"
                        >
                          <Play className="h-3.5 w-3.5 text-[#38BDF8]" />
                          <span>Validate Snapshot</span>
                        </Button>
                      )}

                      {/* If pending review, allow Approve or Reject */}
                      {isPending && (
                        <>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleOpenAction(r, "reject")}
                            className="text-xs gap-1.5"
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                            <span>Reject</span>
                          </Button>
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => handleOpenAction(r, "approve")}
                            className="text-xs gap-1.5 font-semibold"
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                            <span>Approve Patch</span>
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Review Decision Modal */}
      <Dialog
        isOpen={Boolean(actionType)}
        onClose={handleCloseModal}
        title={actionType === "approve" ? "Approve Remediation Patch" : "Reject Remediation Proposal"}
        description={
          actionType === "approve"
            ? "Approving this proposal will confirm reviewer authorization and initiate isolated Playwright axe-core snapshot validation."
            : "Please provide a reason or note explaining why this proposal was rejected."
        }
      >
        <div className="space-y-4 pt-2">
          <div>
            <label
              htmlFor="review-notes"
              className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
            >
              Reviewer Notes (Optional)
            </label>
            <textarea
              id="review-notes"
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Optional review rationale or feedback..."
              className="w-full rounded-lg border border-[#303741] bg-[#171C23] p-2.5 text-xs text-[#F3F4F6] placeholder:text-[#6B7280] focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#303741]">
            <Button variant="outline" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant={actionType === "approve" ? "default" : "destructive"}
              onClick={handleConfirmDecision}
              disabled={approveMutation.isPending || rejectMutation.isPending}
              className={actionType === "approve" ? "font-semibold" : ""}
            >
              {actionType === "approve" ? "Confirm Approval" : "Confirm Rejection"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Live Comparison Modal */}
      <LiveComparisonModal
        remediationId={comparisonRemediationId}
        isOpen={Boolean(comparisonRemediationId)}
        onClose={() => setComparisonRemediationId(null)}
        onApprove={(id) => {
          const target = remediations.find((rem) => rem.id === id);
          if (target) handleOpenAction(target, "approve");
        }}
        onReject={(id) => {
          const target = remediations.find((rem) => rem.id === id);
          if (target) handleOpenAction(target, "reject");
        }}
        isPendingApproval={
          remediations.find((rem) => rem.id === comparisonRemediationId)?.status ===
          "pending_approval"
        }
      />
    </div>
  );
}
