import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { useAuthStore } from "./store/authStore";

describe("App Shell and Routing", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.history.pushState({}, "Test", "/");
    vi.spyOn(useAuthStore.getState(), "checkAuth").mockImplementation(async () => {});
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("renders public landing page at root route for unauthenticated visitors", async () => {
    window.history.pushState({}, "Test", "/");
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Automated Web Accessibility/i })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Get Started/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Sign In/i }).length).toBeGreaterThan(0);
  });

  it("redirects unauthenticated users trying to access protected routes to login page", async () => {
    window.history.pushState({}, "Test", "/app/overview");
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Sign in to AccessGuard AI/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  it(
    "renders protected app shell when authenticated",
    async () => {
      window.history.pushState({}, "Test", "/app/overview");
      useAuthStore.setState({
        user: {
          id: "usr_123",
          email: "alice@company.com",
          display_name: "Alice Engineer",
          is_active: true,
          is_superuser: false,
          created_at: "2026-10-31T00:00:00Z",
          updated_at: "2026-10-31T00:00:00Z",
        },
        accessToken: "mock.jwt.token",
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      render(<App />);
      expect(
        await screen.findByRole("heading", { name: /Accessibility Overview/i }, { timeout: 10000 })
      ).toBeInTheDocument();
      expect(screen.getAllByText(/AccessGuard AI/i).length).toBeGreaterThan(0);
      expect(screen.getAllByRole("link", { name: /Overview/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole("link", { name: /Projects/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole("link", { name: /Scans/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole("link", { name: /Findings/i }).length).toBeGreaterThan(0);
      expect(screen.getAllByRole("link", { name: /AI Remediation/i }).length).toBeGreaterThan(0);
    },
    15000
  );
});
