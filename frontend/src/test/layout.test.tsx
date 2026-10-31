import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppLayout } from "../components/layout/AppLayout";

describe("AppLayout Accessibility and Navigation", () => {
  it("provides an accessible skip to content link", () => {
    render(
      <BrowserRouter>
        <AppLayout
          user={{ email: "user@example.com", display_name: "Test User" }}
        />
      </BrowserRouter>
    );

    const skipLink = screen.getByRole("link", { name: /Skip to main content/i });
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute("href", "#main-content");
  });

  it("toggles mobile drawer navigation menu", async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <AppLayout
          user={{ email: "user@example.com", display_name: "Test User" }}
        />
      </BrowserRouter>
    );

    const menuToggle = screen.getByRole("button", { name: /Open navigation menu/i });
    expect(menuToggle).toHaveAttribute("aria-expanded", "false");

    await user.click(menuToggle);

    expect(
      screen.getByRole("button", { name: /Close navigation menu/i })
    ).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("navigation", { name: /Mobile Navigation/i })).toBeInTheDocument();
  });

  it("calls onLogout callback when signing out", async () => {
    const user = userEvent.setup();
    const mockLogout = vi.fn();

    render(
      <BrowserRouter>
        <AppLayout
          user={{ email: "user@example.com", display_name: "Test User" }}
          onLogout={mockLogout}
        />
      </BrowserRouter>
    );

    const signOutBtn = screen.getByRole("button", { name: /Sign out of account/i });
    await user.click(signOutBtn);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
