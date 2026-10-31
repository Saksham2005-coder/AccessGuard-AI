import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Code,
  FileCheck2,
  RefreshCw,
  ShieldCheck,
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

export function RemediationsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedRemediation, setSelectedRemediation] = useState<Remediation | null>(null);
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
        return <Badge variant="success" className="gap-1"><CheckCircle2 className="h-3 w-3" /> Validated</Badge>;
      case "approved":
        return <Badge variant="primary" className="gap-1"><ShieldCheck className="h-3 w-3" /> Approved</Badge>;
      case "rejected":
        return <Badge variant="critical" className="gap-1"><XCircle className="h-3 w-3" /> Rejected</Badge>;
      case "validation_failed":
        return <Badge variant="critical" className="gap-1"><AlertTriangle className="h-3 w-3" /> Validation Failed</Badge>;
      default:
        return <Badge variant="warning" className="gap-1"><Clock className="h-3 w-3" /> Pending Review</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            AI Remediation Review
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Review evidence-grounded code proposals, approve safe patches, and verify snapshot tests.
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20"
            aria-label="Filter proposals by status"
          >
            <option value="">All Proposals</option>
            <option value="pending_approval">Pending Review</option>
            <option value="approved">Approved</option>
            <option value="validated">Validated</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <Card key={i} className="p-6 space-y-4">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-4 w-2/3" />
              <div className="grid grid-cols-2 gap-4 pt-3">
                <Skeleton className="h-28 w-full" />
                <Skeleton className="h-28 w-full" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {isError && (
        <Card className="border-red-200 bg-red-50 p-6 text-center text-red-800 text-sm">
          Failed to load remediation proposals. Please ensure your session is active.
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && remediations.length === 0 && (
        <EmptyState
          icon={Sparkles}
          title={statusFilter ? "No matching proposals" : "No remediation proposals yet"}
          description={
            statusFilter
              ? "No proposals match the selected status filter."
              : "Generate an AI proposal from any accessibility finding to preview safe patches and isolated snapshot validation."
          }
        />
      )}

      {/* Remediation Cards */}
      {!isLoading && !isError && remediations.length > 0 && (
        <div className="space-y-6">
          {remediations.map((r) => {
            const isPending = r.status === "pending_approval";
            const latestValidation = r.validation_results?.[r.validation_results.length - 1];

            return (
              <Card key={r.id} className="border-slate-200 shadow-xs overflow-hidden">
                <CardContent className="p-6 space-y-5">
                  {/* Proposal Header */}
                  <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-slate-100">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900 text-sm">
                          Remediation Proposal
                        </span>
                        {getStatusBadge(r.status)}
                      </div>
                      <p className="text-xs text-slate-500">
                        Model: <span className="font-mono">{r.model_provider || "AI Provider"}: {r.model_name || "default"}</span>
                        {r.confidence && (
                          <span className="ml-3 font-medium text-indigo-600">
                            {Math.round(r.confidence * 100)}% Confidence
                          </span>
                        )}
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      {isPending && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenAction(r, "reject")}
                            className="gap-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                            <span>Reject</span>
                          </Button>
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleOpenAction(r, "approve")}
                            className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                            <span>Approve Patch</span>
                          </Button>
                        </>
                      )}

                      {r.status === "approved" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => validateMutation.mutate(r.id)}
                          disabled={validateMutation.isPending}
                          className="gap-1.5 text-xs"
                        >
                          <RefreshCw
                            className={`h-3.5 w-3.5 ${validateMutation.isPending ? "animate-spin" : ""}`}
                          />
                          <span>Validate Snapshot</span>
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Root Cause & Recommendation */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1">
                      <span className="font-semibold text-slate-700 uppercase tracking-wider text-[11px]">
                        Likely Root Cause
                      </span>
                      <p className="text-slate-600 leading-relaxed">{r.root_cause}</p>
                    </div>

                    <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1">
                      <span className="font-semibold text-slate-700 uppercase tracking-wider text-[11px]">
                        Engineering Recommendation
                      </span>
                      <p className="text-slate-600 leading-relaxed">{r.recommendation}</p>
                    </div>
                  </div>

                  {/* Before / After Diff Viewer */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                      <Code className="h-3.5 w-3.5 text-slate-400" />
                      <span>Proposed DOM Patch Comparison</span>
                    </span>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                      {/* Before Snippet */}
                      <div className="rounded-lg border border-red-200 overflow-hidden bg-slate-900">
                        <div className="bg-red-950/60 px-3 py-1.5 border-b border-red-900/50 text-[11px] font-medium text-red-300 flex items-center justify-between">
                          <span>Original Failing Snippet</span>
                          <span className="text-[10px] uppercase font-mono text-red-400">Before</span>
                        </div>
                        <pre className="p-3 font-mono text-xs text-red-300 overflow-x-auto whitespace-pre-wrap break-all">
                          {r.before_snippet || "No before snippet provided"}
                        </pre>
                      </div>

                      {/* After Snippet */}
                      <div className="rounded-lg border border-emerald-200 overflow-hidden bg-slate-900">
                        <div className="bg-emerald-950/60 px-3 py-1.5 border-b border-emerald-900/50 text-[11px] font-medium text-emerald-300 flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <span>Remediated Safe Patch</span>
                            <ArrowRight className="h-3 w-3" />
                          </span>
                          <span className="text-[10px] uppercase font-mono text-emerald-400">After</span>
                        </div>
                        <pre className="p-3 font-mono text-xs text-emerald-300 overflow-x-auto whitespace-pre-wrap break-all">
                          {r.after_snippet || "No after snippet provided"}
                        </pre>
                      </div>
                    </div>
                  </div>

                  {/* Validation Results Audit */}
                  {latestValidation && (
                    <div
                      className={`p-3.5 rounded-lg border text-xs flex items-center justify-between ${
                        latestValidation.passed
                          ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                          : "border-red-200 bg-red-50 text-red-900"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {latestValidation.passed ? (
                          <FileCheck2 className="h-4 w-4 text-emerald-600 shrink-0" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
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
                      <span className="text-[11px] text-slate-500 font-mono">
                        {new Date(latestValidation.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  )}

                  {/* Human Approvals Audit Log */}
                  {r.approvals?.length > 0 && (
                    <div className="pt-2 text-xs text-slate-500 border-t border-slate-100 flex items-center justify-between">
                      <span>
                        Reviewed by tenant:{" "}
                        <strong className="capitalize text-slate-700">
                          {r.approvals[r.approvals.length - 1].decision}
                        </strong>
                        {r.approvals[r.approvals.length - 1].comments && (
                          <span className="italic ml-2 text-slate-600">
                            &ldquo;{r.approvals[r.approvals.length - 1].comments}&rdquo;
                          </span>
                        )}
                      </span>
                      <span>
                        {new Date(r.approvals[r.approvals.length - 1].created_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
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
              className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
            >
              Reviewer Notes (Optional)
            </label>
            <textarea
              id="review-notes"
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Add rationale, context, or feedback for this patch..."
              className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant={actionType === "approve" ? "default" : "destructive"}
              onClick={handleConfirmDecision}
              disabled={approveMutation.isPending || rejectMutation.isPending}
              className={actionType === "approve" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
            >
              {actionType === "approve" ? "Confirm Approval" : "Confirm Rejection"}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
