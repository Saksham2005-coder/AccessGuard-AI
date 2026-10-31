import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ScansPage } from "../pages/ScansPage";
import { CreateScanModal } from "../components/scans/CreateScanModal";
import { ScanDetailModal } from "../components/scans/ScanDetailModal";
import * as scansApi from "../api/scans";
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

describe("Scans Execution Journey", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders scan history table with metrics and status", async () => {
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
        config: { max_pages: 10, max_depth: 2 },
        started_at: "2026-10-31T01:00:00Z",
        completed_at: "2026-10-31T01:02:00Z",
        total_pages: 10,
        pages_succeeded: 10,
        pages_failed: 0,
        total_violations: 5,
        axe_version: "4.14.0",
        browser_version: "Chromium 131",
        error_code: null,
        error_summary: null,
        created_at: "2026-10-31T01:00:00Z",
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

    renderWithProviders(<ScansPage />);

    expect(await screen.findByText("https://acme.com")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /View Telemetry/i })).toBeInTheDocument();
  });

  it("disables scan launch when project domain is not verified", () => {
    const unverifiedProjects: projectsApi.Project[] = [
      {
        id: "proj_unverified",
        name: "Unverified Portal",
        base_domain: "unverified.com",
        is_verified: false,
        latest_verification: null,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
        archived_at: null,
      },
    ];

    renderWithProviders(
      <CreateScanModal
        isOpen={true}
        onClose={vi.fn()}
        projects={unverifiedProjects}
        onScanCreated={vi.fn()}
      />
    );

    const startBtn = screen.getByRole("button", { name: /Start Scan/i });
    expect(startBtn).toBeDisabled();
    expect(
      screen.getByText(/Complete DNS TXT verification before running scans/i)
    ).toBeInTheDocument();
  });

  it("renders telemetry details in ScanDetailModal", async () => {
    const mockScan: scansApi.Scan = {
      id: "scan_active",
      project_id: "proj_1",
      requested_by: "usr_1",
      target_url: "https://acme.com",
      status: "running",
      config: { max_pages: 20, max_depth: 2 },
      started_at: "2026-10-31T02:00:00Z",
      completed_at: null,
      total_pages: 5,
      pages_succeeded: 5,
      pages_failed: 0,
      total_violations: 3,
      axe_version: "4.14.0",
      browser_version: "Chromium 131",
      error_code: null,
      error_summary: null,
      created_at: "2026-10-31T02:00:00Z",
    };

    vi.spyOn(scansApi, "getScanApi").mockResolvedValue(mockScan);

    renderWithProviders(
      <ScanDetailModal
        scanId="scan_active"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(await screen.findByText("running")).toBeInTheDocument();
    expect(screen.getByText("Pages Crawled")).toBeInTheDocument();
    expect(screen.getByText("Violations Found")).toBeInTheDocument();
    expect(screen.getByText("axe-core Version")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cancel Scan/i })).toBeInTheDocument();
  });
});
