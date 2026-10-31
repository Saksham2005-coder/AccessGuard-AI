import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectsPage } from "../pages/ProjectsPage";
import { CreateProjectModal } from "../components/projects/CreateProjectModal";
import { DomainVerificationModal } from "../components/projects/DomainVerificationModal";
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

describe("Projects Management Journey", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders projects list with verification badges", async () => {
    const mockProjects: projectsApi.Project[] = [
      {
        id: "proj_1",
        name: "Acme Production App",
        base_domain: "acme.com",
        is_verified: true,
        latest_verification: {
          id: "ver_1",
          project_id: "proj_1",
          domain: "acme.com",
          record_name: "_accessguard-challenge.acme.com",
          record_type: "TXT",
          expected_value: "accessguard-verification=mock-token-1",
          status: "verified",
          expires_at: "2026-11-30T00:00:00Z",
          verified_at: "2026-10-31T00:00:00Z",
          created_at: "2026-10-31T00:00:00Z",
        },
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
        archived_at: null,
      },
      {
        id: "proj_2",
        name: "Beta Portal",
        base_domain: "beta.mysite.org",
        is_verified: false,
        latest_verification: {
          id: "ver_2",
          project_id: "proj_2",
          domain: "beta.mysite.org",
          record_name: "_accessguard-challenge.beta.mysite.org",
          record_type: "TXT",
          expected_value: "accessguard-verification=mock-token-2",
          status: "pending",
          expires_at: "2026-11-30T00:00:00Z",
          verified_at: null,
          created_at: "2026-10-31T00:00:00Z",
        },
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
        archived_at: null,
      },
    ];

    vi.spyOn(projectsApi, "listProjectsApi").mockResolvedValue({
      items: mockProjects,
      total: 2,
    });

    renderWithProviders(<ProjectsPage />);

    expect(await screen.findByText("Acme Production App")).toBeInTheDocument();
    expect(screen.getByText("beta.mysite.org")).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getByText("Pending DNS")).toBeInTheDocument();
  });

  it("validates form inputs in CreateProjectModal", async () => {
    const user = userEvent.setup();
    const handleCreated = vi.fn();
    const handleClose = vi.fn();

    renderWithProviders(
      <CreateProjectModal
        isOpen={true}
        onClose={handleClose}
        onProjectCreated={handleCreated}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Create Project/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Project name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Domain is required/i)).toBeInTheDocument();
    });

    // Enter invalid domain
    const domainInput = screen.getByLabelText(/Target Base Domain/i);
    await user.type(domainInput, "not a valid domain!!");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Please enter a valid domain/i)
      ).toBeInTheDocument();
    });
  });

  it("displays DNS TXT record instructions in DomainVerificationModal", () => {
    const mockProject: projectsApi.Project = {
      id: "proj_10",
      name: "Staging App",
      base_domain: "staging.example.com",
      is_verified: false,
      latest_verification: {
        id: "ver_10",
        project_id: "proj_10",
        domain: "staging.example.com",
        record_name: "_accessguard-challenge.staging.example.com",
        record_type: "TXT",
        expected_value: "accessguard-verification=challenge-val-99",
        status: "pending",
        expires_at: "2026-11-30T00:00:00Z",
        verified_at: null,
        created_at: "2026-10-31T00:00:00Z",
      },
      created_at: "2026-10-31T00:00:00Z",
      updated_at: "2026-10-31T00:00:00Z",
      archived_at: null,
    };

    renderWithProviders(
      <DomainVerificationModal
        project={mockProject}
        isOpen={true}
        onClose={vi.fn()}
        onProjectUpdated={vi.fn()}
      />
    );

    expect(
      screen.getByText(/Domain Verification: staging.example.com/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("_accessguard-challenge.staging.example.com")
    ).toBeInTheDocument();
    expect(
      screen.getByText("accessguard-verification=challenge-val-99")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Verify DNS Now/i })
    ).toBeInTheDocument();
  });
});
