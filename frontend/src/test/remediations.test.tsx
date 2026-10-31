import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RemediationsPage } from "../pages/RemediationsPage";
import * as remediationsApi from "../api/remediations";

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

describe("Remediations Review Journey", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders pending remediation proposal and safe patch diff", async () => {
    const mockRemediations: remediationsApi.Remediation[] = [
      {
        id: "rem_1",
        finding_id: "find_1",
        status: "pending_approval",
        root_cause: "Image missing alternate text attribute",
        recommendation: "Add descriptive alt attribute",
        patch_format: "safe_dom_patch",
        patch_payload: {
          selector: "img.hero-banner",
          attributes_to_set: { alt: "Company Hero Banner" },
        },
        before_snippet: '<img src="/hero.png">',
        after_snippet: '<img src="/hero.png" alt="Company Hero Banner">',
        confidence: 0.95,
        model_provider: "mock-llm",
        model_name: "deterministic-mock",
        prompt_version: "v1.0",
        approvals: [],
        validation_results: [],
        created_at: "2026-10-31T02:00:00Z",
        updated_at: "2026-10-31T02:00:00Z",
      },
    ];

    vi.spyOn(remediationsApi, "listRemediationsApi").mockResolvedValue(mockRemediations);

    renderWithProviders(<RemediationsPage />);

    expect(await screen.findByText("Image missing alternate text attribute")).toBeInTheDocument();
    expect(screen.getByText("Add descriptive alt attribute")).toBeInTheDocument();
    expect(screen.getByText("95% Confidence")).toBeInTheDocument();
    expect(screen.getByText('<img src="/hero.png">')).toBeInTheDocument();
    expect(screen.getByText('<img src="/hero.png" alt="Company Hero Banner">')).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Approve Patch/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reject/i })).toBeInTheDocument();
  });

  it("opens approval modal, submits reviewer notes, and approves patch", async () => {
    const mockRemediations: remediationsApi.Remediation[] = [
      {
        id: "rem_1",
        finding_id: "find_1",
        status: "pending_approval",
        root_cause: "Image missing alternate text attribute",
        recommendation: "Add descriptive alt attribute",
        patch_format: "safe_dom_patch",
        patch_payload: {
          selector: "img.hero-banner",
          attributes_to_set: { alt: "Company Hero Banner" },
        },
        before_snippet: '<img src="/hero.png">',
        after_snippet: '<img src="/hero.png" alt="Company Hero Banner">',
        confidence: 0.95,
        model_provider: "mock-llm",
        model_name: "deterministic-mock",
        prompt_version: "v1.0",
        approvals: [],
        validation_results: [],
        created_at: "2026-10-31T02:00:00Z",
        updated_at: "2026-10-31T02:00:00Z",
      },
    ];

    vi.spyOn(remediationsApi, "listRemediationsApi").mockResolvedValue(mockRemediations);
    const approveSpy = vi.spyOn(remediationsApi, "approveRemediationApi").mockResolvedValue({
      id: "rem_1",
      finding_id: "find_1",
      status: "approved",
      root_cause: "Image missing alternate text attribute",
      recommendation: "Add descriptive alt attribute",
      patch_format: "safe_dom_patch",
      patch_payload: {},
      before_snippet: '<img src="/hero.png">',
      after_snippet: '<img src="/hero.png" alt="Company Hero Banner">',
      confidence: 0.95,
      model_provider: "mock-llm",
      model_name: "deterministic-mock",
      prompt_version: "v1.0",
      approvals: [
        {
          id: "app_1",
          remediation_id: "rem_1",
          reviewer_id: "usr_1",
          decision: "approved",
          comments: "Looks safe for production",
          created_at: "2026-10-31T02:05:00Z",
        },
      ],
      validation_results: [],
      created_at: "2026-10-31T02:00:00Z",
      updated_at: "2026-10-31T02:05:00Z",
    });

    renderWithProviders(<RemediationsPage />);

    const approveButton = await screen.findByRole("button", { name: /Approve Patch/i });
    fireEvent.click(approveButton);

    expect(screen.getByText("Approve Remediation Patch")).toBeInTheDocument();

    const notesInput = screen.getByLabelText(/Reviewer Notes/i);
    fireEvent.change(notesInput, { target: { value: "Looks safe for production" } });

    const confirmButton = screen.getByRole("button", { name: /Confirm Approval/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(approveSpy).toHaveBeenCalledWith("rem_1", "Looks safe for production");
    });
  });

  it("triggers isolated snapshot validation on approved remediation", async () => {
    const mockRemediations: remediationsApi.Remediation[] = [
      {
        id: "rem_approved",
        finding_id: "find_1",
        status: "approved",
        root_cause: "Image missing alternate text attribute",
        recommendation: "Add descriptive alt attribute",
        patch_format: "safe_dom_patch",
        patch_payload: {
          selector: "img.hero-banner",
          attributes_to_set: { alt: "Company Hero Banner" },
        },
        before_snippet: '<img src="/hero.png">',
        after_snippet: '<img src="/hero.png" alt="Company Hero Banner">',
        confidence: 0.95,
        model_provider: "mock-llm",
        model_name: "deterministic-mock",
        prompt_version: "v1.0",
        approvals: [
          {
            id: "app_1",
            remediation_id: "rem_approved",
            reviewer_id: "usr_1",
            decision: "approved",
            comments: "Verified manually",
            created_at: "2026-10-31T02:05:00Z",
          },
        ],
        validation_results: [
          {
            id: "val_1",
            remediation_id: "rem_approved",
            validation_mode: "isolated_axe_snapshot",
            passed: true,
            original_rule_resolved: true,
            new_violations: [],
            details: { engine: "axe-core 4.14.0" },
            created_at: "2026-10-31T02:06:00Z",
          },
        ],
        created_at: "2026-10-31T02:00:00Z",
        updated_at: "2026-10-31T02:05:00Z",
      },
    ];

    vi.spyOn(remediationsApi, "listRemediationsApi").mockResolvedValue(mockRemediations);
    const validateSpy = vi.spyOn(remediationsApi, "validateRemediationApi").mockResolvedValue({
      ...mockRemediations[0],
      status: "validated",
    });

    renderWithProviders(<RemediationsPage />);

    expect(await screen.findByText("Clean Pass (Original rule resolved, zero regressions)")).toBeInTheDocument();

    const validateBtn = screen.getByRole("button", { name: /Validate Snapshot/i });
    fireEvent.click(validateBtn);

    await waitFor(() => {
      expect(validateSpy).toHaveBeenCalledWith("rem_approved");
    });
  });
});
