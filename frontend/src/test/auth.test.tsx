import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { useAuthStore } from "../store/authStore";

describe("Auth Store & State Management", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("sets user and updates isAuthenticated", () => {
    const mockUser = {
      id: "usr_1",
      email: "test@example.com",
      display_name: "Test User",
      is_active: true,
      is_superuser: false,
      created_at: "2026-10-31T00:00:00Z",
      updated_at: "2026-10-31T00:00:00Z",
    };

    useAuthStore.getState().setUser(mockUser);
    expect(useAuthStore.getState().user).toEqual(mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    useAuthStore.getState().setUser(null);
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("clears error state when clearError is called", () => {
    useAuthStore.setState({ error: "Some error" });
    expect(useAuthStore.getState().error).toBe("Some error");
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});

describe("Protected Route Guard", () => {
  it("renders accessible loading indicator when checking session", () => {
    useAuthStore.setState({ isAuthenticated: false, isLoading: true });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    const statusEl = screen.getByRole("status");
    expect(statusEl).toHaveAttribute("aria-busy", "true");
    expect(statusEl).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText(/Checking session.../i)).toBeInTheDocument();
    expect(screen.queryByText(/Protected Content/i)).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    useAuthStore.setState({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: "usr_1",
        email: "alice@example.com",
        display_name: "Alice",
        is_active: true,
        is_superuser: false,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
      },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText(/Protected Content/i)).toBeInTheDocument();
  });
});

describe("Login and Register Validation", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("validates required fields on login submit", async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const submitBtn = screen.getByRole("button", { name: /Sign in/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/Email Address/i);
    expect(emailInput).toHaveAttribute("aria-invalid", "true");
  });

  it("validates matching passwords on register submit", async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const nameInput = screen.getByLabelText(/Full Name/i);
    const emailInput = screen.getByLabelText(/Email Address/i);
    const passInput = screen.getByLabelText(/^Password$/i);
    const confirmInput = screen.getByLabelText(/Confirm Password/i);
    const submitBtn = screen.getByRole("button", { name: /Create account/i });

    await user.type(nameInput, "Dev User");
    await user.type(emailInput, "dev@example.com");
    await user.type(passInput, "validPassword123");
    await user.type(confirmInput, "differentPassword");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });
});
