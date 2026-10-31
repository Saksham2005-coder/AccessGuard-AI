import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App Shell", () => {
  it("renders brand and navigation links", () => {
    render(<App />);
    expect(screen.getAllByText(/AccessGuard AI/i).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Overview/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Projects/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Scans/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Findings/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /AI Remediation/i }).length).toBeGreaterThan(0);
  });

  it("renders default overview page heading", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { name: /Accessibility Overview/i })
    ).toBeInTheDocument();
  });
});
