import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FindingsPage } from "../pages/FindingsPage";
import { FindingDetailDrawer } from "../components/findings/FindingDetailDrawer";
import * as findingsApi from "../api/findings";
import * as projectsApi from "../api/projects";

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

describe("Findings Explorer Journey", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders findings table and filters by search query", async () => {
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

    const mockFindings: findingsApi.Finding[] = [
      {
        id: "find_1",
        scan_page_id: "sp_1",
        axe_rule_id: "image-alt",
        impact: "critical",
        description: "Images must have alternate text",
        help: "Elements must have an alt attribute",
        help_url: "https://dequeuniversity.com/rules/axe/4.14/image-alt",
        selector: "img.hero-banner",
        html_snippet: '<img src="/hero.png">',
        wcag_tags: ["wcag2a", "wcag111"],
        failure_summary: "Fix alt",
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
        description: "Elements must meet minimum color contrast ratio",
        help: "Ensure contrast ratio of at least 4.5:1",
        help_url: "https://dequeuniversity.com/rules/axe/4.14/color-contrast",
        selector: "button.secondary",
        html_snippet: '<button class="secondary">Cancel</button>',
        wcag_tags: ["wcag2aa", "wcag143"],
        failure_summary: "Fix contrast",
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

    vi.spyOn(findingsApi, "listFindingsApi").mockResolvedValue({
      items: mockFindings,
      total: 2,
    });

    renderWithProviders(<FindingsPage />);

    expect(await screen.findByText("image-alt")).toBeInTheDocument();
    expect(screen.getByText("color-contrast")).toBeInTheDocument();
    expect(screen.getByText("Images must have alternate text")).toBeInTheDocument();

    // Filter using search query input
    const searchInput = screen.getByPlaceholderText(/Search rule ID or selector/i);
    fireEvent.change(searchInput, { target: { value: "image-alt" } });

    await waitFor(() => {
      expect(screen.getByText("image-alt")).toBeInTheDocument();
      expect(screen.queryByText("color-contrast")).not.toBeInTheDocument();
    });
  });

  it("opens FindingDetailDrawer and shows WCAG tags and selector", async () => {
    const mockFindingDetail: findingsApi.FindingDetail = {
      id: "find_1",
      scan_page_id: "sp_1",
      axe_rule_id: "image-alt",
      impact: "critical",
      description: "Images must have alternate text",
      help: "Elements must have an alt attribute",
      help_url: "https://dequeuniversity.com/rules/axe/4.14/image-alt",
      selector: "img.hero-banner",
      html_snippet: '<img src="/hero.png">',
      wcag_tags: ["wcag2a", "wcag111"],
      failure_summary: "Fix any of the following: Element does not have an alt attribute",
      fingerprint: "fp_1",
      is_incomplete: false,
      nodes: [],
      created_at: "2026-10-31T01:00:00Z",
      updated_at: "2026-10-31T01:00:00Z",
    };

    const handleRemediate = vi.fn();
    const handleClose = vi.fn();

    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });

    renderWithProviders(
      <FindingDetailDrawer
        finding={mockFindingDetail}
        isOpen={true}
        onClose={handleClose}
        onRequestRemediation={handleRemediate}
      />
    );

    expect(screen.getByText("Finding: image-alt")).toBeInTheDocument();
    expect(screen.getByText("wcag111")).toBeInTheDocument();
    expect(screen.getByText("img.hero-banner")).toBeInTheDocument();

    // Copy selector
    const copyButton = screen.getByRole("button", { name: /Copy element selector/i });
    fireEvent.click(copyButton);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("img.hero-banner");

    // Click Generate AI Remediation
    const remediateButton = screen.getByRole("button", { name: /Generate AI Remediation/i });
    fireEvent.click(remediateButton);
    expect(handleRemediate).toHaveBeenCalledWith("find_1");
    expect(handleClose).toHaveBeenCalled();
  });
});
