import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReportsPage } from "../pages/ReportsPage";
import * as projectsApi from "../api/projects";
import * as scansApi from "../api/scans";
import * as findingsApi from "../api/findings";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe("Compliance Reports Journey", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calculates compliance health score and renders WCAG principle breakdowns", async () => {
    const mockProjects: projectsApi.Project[] = [
      {
        id: "proj_1",
        name: "Acme App",
        base_domain: "acme.com",
        is_verified: true,
        latest_verification: null,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
        archived_at: null,
      },
    ];

    const mockScans: scansApi.Scan[] = [
      {
        id: "scan_1",
        project_id: "proj_1",
        requested_by: "usr_1",
        target_url: "https://acme.com",
        status: "completed",
        config: {},
        started_at: "2026-10-31T01:00:00Z",
        completed_at: "2026-10-31T01:02:00Z",
        total_pages: 5,
        pages_succeeded: 5,
        pages_failed: 0,
        total_violations: 2,
        axe_version: "4.14.0",
        browser_version: "Chromium 131",
        error_code: null,
        error_summary: null,
        created_at: "2026-10-31T01:00:00Z",
      },
    ];

    const mockFindings: findingsApi.Finding[] = [
      {
        id: "find_1",
        scan_page_id: "sp_1",
        axe_rule_id: "image-alt",
        impact: "critical",
        description: "Images must have alternate text",
        help: "Alt text required",
        help_url: null,
        selector: "img",
        html_snippet: "<img />",
        wcag_tags: ["wcag2a", "wcag111"],
        failure_summary: "Alt required",
        fingerprint: "fp_1",
        is_incomplete: false,
        created_at: "2026-10-31T01:00:00Z",
        updated_at: "2026-10-31T01:00:00Z",
      },
      {
        id: "find_2",
        scan_page_id: "sp_1",
        axe_rule_id: "color-contrast",
        impact: "serious",
        description: "Low contrast ratio",
        help: "Contrast ratio insufficient",
        help_url: null,
        selector: "button",
        html_snippet: "<button>Submit</button>",
        wcag_tags: ["wcag2aa", "wcag143"],
        failure_summary: "Contrast low",
        fingerprint: "fp_2",
        is_incomplete: false,
        created_at: "2026-10-31T01:00:00Z",
        updated_at: "2026-10-31T01:00:00Z",
      },
    ];

    vi.spyOn(projectsApi, "listProjectsApi").mockResolvedValue({
      items: mockProjects,
      total: 1,
    });

    vi.spyOn(scansApi, "listProjectScansApi").mockResolvedValue({
      items: mockScans,
      total: 1,
    });

    vi.spyOn(findingsApi, "listFindingsApi").mockResolvedValue({
      items: mockFindings,
      total: 2,
    });

    // Mock window.print
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});

    renderWithProviders(<ReportsPage />);

    // Critical (15) + Serious (8) = 23 penalty -> 100 - 23 = 77
    expect(await screen.findByText(/77/)).toBeInTheDocument();
    expect(screen.getByText("Critical Issues")).toBeInTheDocument();
    expect(screen.getByText("1. Perceivable")).toBeInTheDocument();

    // Trigger Print
    const printButton = screen.getByRole("button", { name: /Print Report/i });
    fireEvent.click(printButton);
    expect(printSpy).toHaveBeenCalled();
  });
});
