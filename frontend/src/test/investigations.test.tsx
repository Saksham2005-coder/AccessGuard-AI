import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AutonomousInvestigationPanel } from "../components/investigations/AutonomousInvestigationPanel";
import * as api from "../api/investigations";

vi.mock("../api/investigations", () => ({
  getLatestInvestigation: vi.fn(),
  triggerInvestigation: vi.fn(),
}));

const mockReport: api.InvestigationReport = {
  investigation_id: "inv-test-123",
  scan_id: "scan-test-123",
  status: "partial",
  overall_confidence: "tentative",
  executive_summary: "Autonomous multi-agent investigation completed across 5 dimensions with 2 critical barriers.",
  duration_ms: 120,
  created_at: "2026-11-01T12:00:00Z",
  manual_verification_checklist: [
    "Verify color contrast over CSS gradients with a calibrated color picker.",
    "Perform manual NVDA/JAWS screen reader verification on custom widgets.",
  ],
  wcag_citations: [
    {
      criterion_id: "1.4.3",
      title: "Contrast (Minimum)",
      level: "AA",
      summary: "Contrast at least 4.5:1",
      url: "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
    },
  ],
  specialists: {
    contrast_investigator: {
      agent_id: "contrast_investigator",
      agent_name: "Contrast & Visual Acoustics Investigator",
      agent_version: "1.0.0",
      dimension: "color_contrast",
      status: "completed",
      confidence: "supported",
      findings_count: 1,
      observations: [
        {
          finding_id: "f-1",
          rule_id: "color-contrast",
          selector: ".hero-title",
          summary: "Insufficient contrast ratio on element",
          details: "Measured 2.1:1 ratio",
          severity: "serious",
        },
      ],
      recommendations: [
        {
          title: "Increase text luminance contrast",
          action: "Adjust CSS color",
          code_example: "color: #111;",
          priority: "P1",
          affected_finding_ids: ["f-1"],
        },
      ],
      wcag_criteria: ["1.4.3"],
      limitations: ["Color contrast calculation relies on static CSS."],
      evidence_references: ["f-1"],
    },
    keyboard_investigator: {
      agent_id: "keyboard_investigator",
      agent_name: "Keyboard Navigation & Focus Trap Investigator",
      agent_version: "1.0.0",
      dimension: "keyboard_accessibility",
      status: "skipped",
      confidence: "insufficient_evidence",
      findings_count: 0,
      observations: [],
      recommendations: [],
      wcag_criteria: ["2.1.1"],
      limitations: [
        "No deterministic keyboard navigation session was recorded for this scan. Automated DOM analysis cannot determine focus trap without an interactive keyboard test run.",
      ],
      evidence_references: [],
    },
  },
  remediation_matrix: [
    {
      priority: "P1",
      title: "Increase text luminance contrast",
      description: "Adjust CSS color to meet 4.5:1",
      dimension: "color_contrast",
      affected_findings: ["f-1"],
      remediation_hint: "color: #111827;",
    },
    {
      priority: "P3",
      title: "Execute interactive keyboard navigation test session",
      description: "Run simulator",
      dimension: "keyboard_accessibility",
      affected_findings: [],
      remediation_hint: "Run keyboard test session",
    },
  ],
};

describe("AutonomousInvestigationPanel Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state when no report exists", async () => {
    vi.mocked(api.getLatestInvestigation).mockRejectedValueOnce(new Error("Not found"));

    render(<AutonomousInvestigationPanel scanId="scan-123" />);

    expect(await screen.findByText(/No Investigation Conducted Yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start Investigation Now/i })).toBeInTheDocument();
  });

  it("renders complete investigation report with specialists, checklist, and disclaimer", async () => {
    vi.mocked(api.getLatestInvestigation).mockResolvedValueOnce(mockReport);

    render(<AutonomousInvestigationPanel scanId="scan-123" />);

    // Header and confidence
    expect(await screen.findByText(/Autonomous Accessibility Agents/i)).toBeInTheDocument();
    expect(screen.getByText(/Confidence: tentative/i)).toBeInTheDocument();

    // Executive synthesis
    expect(screen.getByText(/Autonomous multi-agent investigation completed across 5 dimensions/i)).toBeInTheDocument();

    // Enterprise assistive tech disclaimer
    expect(screen.getByText(/Assistive Technology Notice:/i)).toBeInTheDocument();
    expect(screen.getByText(/do not constitute an actual NVDA, JAWS, or VoiceOver execution/i)).toBeInTheDocument();

    // Manual verification checklist

    expect(screen.getByText(/Manual Verification Checklist/i)).toBeInTheDocument();
    expect(screen.getByText(/Verify color contrast over CSS gradients/i)).toBeInTheDocument();

    // Specialist cards
    expect(screen.getByText(/Contrast & Visual Acoustics Investigator/i)).toBeInTheDocument();
    expect(screen.getByText(/Keyboard Navigation & Focus Trap Investigator/i)).toBeInTheDocument();
    expect(screen.getByText(/Dimension Skipped:/i)).toBeInTheDocument();

    // Prioritized remediation matrix
    expect(screen.getByText(/Prioritized Remediation Matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/Increase text luminance contrast/i)).toBeInTheDocument();
  });

  it("triggers new investigation when action button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getLatestInvestigation).mockResolvedValueOnce(mockReport);
    vi.mocked(api.triggerInvestigation).mockResolvedValueOnce({
      ...mockReport,
      executive_summary: "Re-run completed successfully with fresh evidence.",
    });

    render(<AutonomousInvestigationPanel scanId="scan-123" />);

    const reRunBtn = await screen.findByRole("button", { name: /Re-Run Investigation/i });
    await user.click(reRunBtn);

    expect(api.triggerInvestigation).toHaveBeenCalledWith("scan-123", true);
    await waitFor(() => {
      expect(screen.getByText(/Re-run completed successfully with fresh evidence./i)).toBeInTheDocument();
    });
  });

  it("filters remediation matrix by priority tab", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getLatestInvestigation).mockResolvedValueOnce(mockReport);

    render(<AutonomousInvestigationPanel scanId="scan-123" />);

    expect(await screen.findByText(/Increase text luminance contrast/i)).toBeInTheDocument();
    expect(screen.getByText(/Execute interactive keyboard navigation test session/i)).toBeInTheDocument();

    // Filter to P1 only
    const p1Tab = screen.getByRole("button", { name: /^P1$/i });
    await user.click(p1Tab);

    expect(screen.getByText(/Increase text luminance contrast/i)).toBeInTheDocument();
    expect(screen.queryByText(/Execute interactive keyboard navigation test session/i)).not.toBeInTheDocument();
  });
});
