import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { VisualHeatmapViewer } from "../components/heatmap/VisualHeatmapViewer";
import { HeatmapResponse, ScanPageSummary } from "../api/heatmap";

const mockPages: ScanPageSummary[] = [
  {
    id: "page-1",
    scan_id: "scan-1",
    url: "https://example.com",
    status: "audited",
    title: "Example Domain",
    violations_count: 2,
    has_screenshot: true,
    viewport_width: 1280,
    viewport_height: 800,
  },
];

const mockHeatmapData: HeatmapResponse = {
  page_id: "page-1",
  url: "https://example.com",
  screenshot_url: "/api/v1/scans/scan-1/pages/page-1/screenshot",
  viewport: {
    width: 1280,
    height: 800,
    device_pixel_ratio: 1.0,
  },
  markers: [
    {
      finding_id: "find-1",
      rule_id: "color-contrast",
      impact: "serious",
      description: "Element has insufficient color contrast",
      help_url: "https://dequeuniversity.com/rules/axe/4.14/color-contrast",
      selector: "button.submit-btn",
      html: "<button class='submit-btn'>Submit</button>",
      bounding_box: { x: 100, y: 150, width: 80, height: 32 },
      geometry_status: "located",
    },
    {
      finding_id: "find-2",
      rule_id: "image-alt",
      impact: "critical",
      description: "Images must have alternate text",
      help_url: "https://dequeuniversity.com/rules/axe/4.14/image-alt",
      selector: "img.hero-avatar",
      html: "<img src='avatar.png' class='hero-avatar'>",
      bounding_box: null,
      geometry_status: "missing_target",
    },
  ],
  density_points: [
    { x: 140, y: 166, weight: 0.8, radius: 45 },
  ],
  total_violations: 2,
  located_count: 1,
  unlocated_count: 1,
};

describe("VisualHeatmapViewer", () => {
  it("renders visual canvas overlay mode with finding markers and unlocated notices", () => {
    const handleSelectPage = vi.fn();

    render(
      <VisualHeatmapViewer
        heatmapData={mockHeatmapData}
        pages={mockPages}
        selectedPageId="page-1"
        onSelectPage={handleSelectPage}
      />
    );

    // Should render rule items in list
    expect(screen.getByText(/color-contrast/i)).toBeInTheDocument();
    expect(screen.getAllByText(/image-alt/i).length).toBeGreaterThanOrEqual(1);

    // Should indicate unlocated notice
    expect(screen.getByText(/could not be visually anchored/i)).toBeInTheDocument();
  });

  it("filters markers when severity filter is clicked", () => {
    render(
      <VisualHeatmapViewer
        heatmapData={mockHeatmapData}
        pages={mockPages}
        selectedPageId="page-1"
        onSelectPage={vi.fn()}
      />
    );

    // Initially 2 violations
    expect(screen.getByText(/All Violations \(2\)/i)).toBeInTheDocument();

    // Click critical filter
    const criticalBtn = screen.getByRole("button", { name: /^critical$/i });
    fireEvent.click(criticalBtn);

    // Now only 1 violation shown
    expect(screen.getByText(/All Violations \(1\)/i)).toBeInTheDocument();
  });

  it("switches to accessible table view and displays coordinates", () => {
    render(
      <VisualHeatmapViewer
        heatmapData={mockHeatmapData}
        pages={mockPages}
        selectedPageId="page-1"
        onSelectPage={vi.fn()}
      />
    );

    // Switch to Accessible Table
    const tableToggleBtn = screen.getByTitle(/Accessible Table Fallback/i);
    fireEvent.click(tableToggleBtn);

    // Should render accessible table header
    expect(screen.getByText(/Accessible Heatmap Telemetry Table/i)).toBeInTheDocument();
    expect(screen.getByText("button.submit-btn")).toBeInTheDocument();
    expect(screen.getByText("100, 150, 80, 32")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("selects marker and triggers onInspectFinding", () => {
    const handleInspect = vi.fn();

    render(
      <VisualHeatmapViewer
        heatmapData={mockHeatmapData}
        pages={mockPages}
        selectedPageId="page-1"
        onSelectPage={vi.fn()}
        onInspectFinding={handleInspect}
      />
    );

    // Click on color-contrast item to select it
    const item = screen.getByText(/color-contrast/i);
    fireEvent.click(item);

    // Now inspect button should appear in detail card
    const inspectBtn = screen.getByRole("button", { name: /Inspect/i });
    fireEvent.click(inspectBtn);

    expect(handleInspect).toHaveBeenCalledWith("find-1");
  });

  it("handles loading and empty states cleanly", () => {
    const { rerender } = render(
      <VisualHeatmapViewer
        heatmapData={null}
        pages={[]}
        selectedPageId=""
        onSelectPage={vi.fn()}
        isLoading={true}
      />
    );

    expect(screen.getByText(/Loading visual accessibility heatmap telemetry/i)).toBeInTheDocument();

    rerender(
      <VisualHeatmapViewer
        heatmapData={null}
        pages={[]}
        selectedPageId=""
        onSelectPage={vi.fn()}
        isLoading={false}
      />
    );

    expect(screen.getByText(/Heatmap Data Unavailable/i)).toBeInTheDocument();
  });
});
