import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import App from "./App";
import { useAuthStore } from "./store/authStore";

describe("App Shell and Routing", () => {
  beforeEach(() => {
    window.history.pushState({}, "Test", "/");
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("redirects unauthenticated users to login page", async () => {
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Sign in to AccessGuard AI/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  it("renders protected app shell when authenticated", async () => {
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
    expect(await screen.findByRole("heading", { name: /Accessibility Overview/i })).toBeInTheDocument();
    expect(screen.getAllByText(/AccessGuard AI/i).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Overview/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Projects/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Scans/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Findings/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /AI Remediation/i }).length).toBeGreaterThan(0);
  });
});
