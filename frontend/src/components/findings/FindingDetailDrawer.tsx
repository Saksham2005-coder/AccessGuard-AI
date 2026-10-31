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
      <div className="space-y-4 pt-2">
        {/* Severity & Criteria Header Banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-[#303741] bg-[#171C23]">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#9CA3AF] font-medium">Impact Severity:</span>
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
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#38BDF8] hover:underline"
            >
              <span>axe-core Rule Guidance</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>

        {/* WCAG Tags Pill Row */}
        {finding.wcag_tags && finding.wcag_tags.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              WCAG Standard Mapping
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {finding.wcag_tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-md bg-[#252C35] border border-[#303741] text-[11px] font-mono text-[#F3F4F6]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Target DOM Element Selector */}
        {finding.selector && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold uppercase tracking-wider text-[#9CA3AF]">
                DOM Element Selector
              </span>
              <button
                type="button"
                onClick={handleCopySelector}
                className="text-[#38BDF8] hover:text-[#0EA5E9] inline-flex items-center gap-1 text-xs transition-colors"
                aria-label="Copy element selector"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? "Copied" : "Copy Selector"}</span>
              </button>
            </div>
            <div className="p-2.5 rounded-lg border border-[#303741] bg-[#111315] font-mono text-xs text-[#38BDF8] break-all select-all">
              {finding.selector}
            </div>
          </div>
        )}

        {/* Offending HTML Snippet */}
        {finding.html_snippet && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
              <Code className="h-3.5 w-3.5 text-[#38BDF8]" />
              <span>Target HTML Snippet</span>
            </div>
            <pre className="p-3 rounded-xl border border-[#303741] bg-[#111315] text-[#F3F4F6] text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all select-all">
              {finding.html_snippet}
            </pre>
          </div>
        )}

        {/* Failure Summary */}
        {finding.failure_summary && (
          <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-xs">
            <div className="font-semibold text-[#FB7185] flex items-center gap-1.5 mb-1">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>axe-core Failure Diagnostics</span>
            </div>
            <p className="text-[#9CA3AF] leading-relaxed whitespace-pre-line font-mono text-[11px]">
              {finding.failure_summary}
            </p>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-[#303741]">
          <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
            Close
          </Button>

          <Button
            type="button"
            size="sm"
            onClick={handleRemediate}
            className="text-xs gap-2 font-semibold shadow-sm"
          >
            <Sparkles className="h-3.5 w-3.5 fill-current" />
            <span>Generate AI Remediation</span>
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
