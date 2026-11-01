import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { LiveComparisonModal } from "../components/remediations/LiveComparisonModal";
import * as remediationsApi from "../api/remediations";

const mockComparisonData: remediationsApi.ComparisonResponse = {
  remediation_id: "rem-1",
  finding_id: "find-1",
  rule_id: "image-alt",
  before_html: '<img src="hero.jpg">',
  after_html: '<img src="hero.jpg" alt="Hero Banner">',
  before_screenshot_url: "/api/v1/remediations/rem-1/screenshots/before",
  after_screenshot_url: "/api/v1/remediations/rem-1/screenshots/after",
  dom_diff: "--- Original Snapshot\n+++ Proposed Patch\n- <img src=\"hero.jpg\">\n+ <img src=\"hero.jpg\" alt=\"Hero Banner\">",
  patch_operations: [
    {
      operation: "set_attribute",
      selector: "img",
      attribute: "alt",
      value: "Hero Banner",
    },
  ],
  original_rule_resolved: true,
  new_violations: [],
  passed: true,
  status: "completed",
  created_at: "2026-11-01T10:00:00Z",
  details: {
    axe_version: "4.14.0",
    duration_ms: 120,
    browser_rendered: true,
  },
};

describe("LiveComparisonModal", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders comparison modal, safety policy banner, and side-by-side snapshots", async () => {
    vi.spyOn(remediationsApi, "getRemediationComparisonApi").mockResolvedValue(mockComparisonData);

    render(
      <LiveComparisonModal
        remediationId="rem-1"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    // Should display policy banner
    expect(
      screen.getByText(/Live production websites are never modified/i)
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Original Snapshot \(Violating\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Proposed Patch \(Compliant\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Resolved 'image-alt' with zero new regressions/i)).toBeInTheDocument();
    });
  });

  it("switches to DOM diff mode and displays unified diff", async () => {
    vi.spyOn(remediationsApi, "getRemediationComparisonApi").mockResolvedValue(mockComparisonData);

    render(
      <LiveComparisonModal
        remediationId="rem-1"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Side-by-Side/i })).toBeInTheDocument();
    });

    const diffBtn = screen.getByRole("button", { name: /DOM Diff/i });
    fireEvent.click(diffBtn);

    expect(screen.getByText(/Unified Diff: Original vs. Patched DOM/i)).toBeInTheDocument();
    expect(screen.getByText(/Hero Banner/i)).toBeInTheDocument();
  });

  it("switches to Re-Audit Details mode and confirms zero regressions", async () => {
    vi.spyOn(remediationsApi, "getRemediationComparisonApi").mockResolvedValue(mockComparisonData);

    render(
      <LiveComparisonModal
        remediationId="rem-1"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Re-Audit Details/i })).toBeInTheDocument();
    });

    const auditBtn = screen.getByRole("button", { name: /Re-Audit Details/i });
    fireEvent.click(auditBtn);

    expect(
      screen.getByText(/Zero new accessibility regressions detected in isolated re-audit/i)
    ).toBeInTheDocument();
  });

  it("triggers approve and reject callbacks when pending approval", async () => {
    vi.spyOn(remediationsApi, "getRemediationComparisonApi").mockResolvedValue(mockComparisonData);
    const handleApprove = vi.fn();
    const handleReject = vi.fn();

    render(
      <LiveComparisonModal
        remediationId="rem-1"
        isOpen={true}
        onClose={vi.fn()}
        onApprove={handleApprove}
        onReject={handleReject}
        isPendingApproval={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Approve Patch/i })).toBeInTheDocument();
    });

    const approveBtn = screen.getByRole("button", { name: /Approve Patch/i });
    fireEvent.click(approveBtn);
    expect(handleApprove).toHaveBeenCalledWith("rem-1");

    const rejectBtn = screen.getByRole("button", { name: /Reject/i });
    fireEvent.click(rejectBtn);
    expect(handleReject).toHaveBeenCalledWith("rem-1");
  });
});
