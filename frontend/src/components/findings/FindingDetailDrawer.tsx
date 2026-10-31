import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  Check,
  Code,
  Copy,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { FindingDetail } from "../../api/findings";

export interface FindingDetailDrawerProps {
  finding: FindingDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onRequestRemediation?: (findingId: string) => void;
}

export function FindingDetailDrawer({
  finding,
  isOpen,
  onClose,
  onRequestRemediation,
}: FindingDetailDrawerProps) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  if (!finding) return null;

  const handleCopySelector = () => {
    if (finding.selector) {
      navigator.clipboard.writeText(finding.selector);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRemediate = () => {
    if (onRequestRemediation) {
      onRequestRemediation(finding.id);
    } else {
      navigate(`/app/remediations?finding_id=${finding.id}`);
    }
    onClose();
  };

  const getImpactBadgeVariant = (impact?: string | null) => {
    switch (impact) {
      case "critical":
        return "critical";
      case "serious":
        return "serious";
      case "moderate":
        return "moderate";
      case "minor":
        return "minor";
      default:
        return "default";
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Finding: ${finding.axe_rule_id}`}
      description={finding.description}
      className="max-w-2xl"
    >
      <div className="space-y-5 pt-2">
        {/* Severity & Criteria Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-lg border border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Impact Severity:</span>
            <Badge
              variant={getImpactBadgeVariant(finding.impact)}
              className="capitalize font-semibold text-xs"
            >
              {finding.impact || "unspecified"}
            </Badge>
          </div>

          {finding.help_url && (
            <a
              href={finding.help_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#4657D8] hover:underline"
            >
              <span>axe-core Rule Guidance</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>

        {/* WCAG Tags */}
        {finding.wcag_tags && finding.wcag_tags.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              WCAG Success Criteria & Guidelines
            </span>
            <div className="flex flex-wrap gap-1.5">
              {finding.wcag_tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Target DOM Selector */}
        {finding.selector && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                DOM Element Selector
              </span>
              <button
                type="button"
                onClick={handleCopySelector}
                className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800"
                aria-label="Copy element selector"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    <span className="text-emerald-600">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-900 p-3 font-mono text-xs text-slate-100 break-all select-all">
              {finding.selector}
            </div>
          </div>
        )}

        {/* HTML Snippet */}
        {finding.html_snippet && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Code className="h-3.5 w-3.5 text-slate-400" />
              <span>Failing HTML Node Snippet</span>
            </span>
            <pre className="rounded-lg border border-slate-200 bg-slate-900 p-3.5 font-mono text-xs text-emerald-400 overflow-x-auto whitespace-pre-wrap break-all">
              {finding.html_snippet}
            </pre>
          </div>
        )}

        {/* Failure Summary */}
        {finding.failure_summary && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3.5 text-xs text-red-800 space-y-1">
            <p className="font-semibold flex items-center gap-1.5">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>Axe Evaluation Failure Summary</span>
            </p>
            <p className="text-slate-700 leading-relaxed whitespace-pre-line pl-5.5">
              {finding.failure_summary}
            </p>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <Button type="button" variant="outline" onClick={onClose}>
            Close
          </Button>

          <Button
            type="button"
            onClick={handleRemediate}
            className="gap-2 bg-gradient-to-r from-[#4657D8] to-indigo-600 hover:from-[#3746B8] hover:to-indigo-700"
          >
            <Sparkles className="h-4 w-4" />
            <span>Generate AI Remediation</span>
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
