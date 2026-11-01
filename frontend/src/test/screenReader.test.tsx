import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ScreenReaderSimulator } from "../components/screenreader/ScreenReaderSimulator";
import * as api from "../api/screenReader";
import { ScanPageSummary } from "../api/heatmap";



vi.mock("../api/screenReader", () => ({

  getScreenReaderSimulationApi: vi.fn(),
}));

const mockSimulationData: api.ScreenReaderSimulationResponse = {
  scan_id: "scan-test-001",
  page_id: "page-test-001",
  page_url: "https://example.com/demo",
  nodes_count: 5,
  captured_at: "2026-11-01T12:00:00Z",
  disclaimer:
    "Screen-reader-oriented reading and navigation preview exposing DOM semantics and reading order. This browser-based preview does NOT emulate NVDA, JAWS, or VoiceOver execution.",
  limitations: [
    "Static DOM interpretation aid based on standard browser accessibility semantics.",
  ],
  reading_order: [
    {
      sequence_index: 0,
      role: "banner",
      accessible_name: "AccessGuard AI Banner",
      description: null,
      heading_level: null,
      landmark_type: "banner",
      is_interactive: false,
      selector: "header",
      tag_name: "header",
      has_name: true,
      attributes: { role: "banner" },
      associated_finding_id: null,
      potential_issue: null,
    },
    {
      sequence_index: 1,
      role: "heading",
      accessible_name: "Main Platform Heading",
      description: null,
      heading_level: 1,
      landmark_type: null,
      is_interactive: false,
      selector: "header > h1",
      tag_name: "h1",
      has_name: true,
      attributes: {},
      associated_finding_id: null,
      potential_issue: null,
    },
    {
      sequence_index: 2,
      role: "heading",
      accessible_name: "Skipped Subsection",
      description: null,
      heading_level: 3,
      landmark_type: null,
      is_interactive: false,
      selector: "main > h3",
      tag_name: "h3",
      has_name: true,
      attributes: {},
      associated_finding_id: "finding-h3-01",
      potential_issue: "Heading level skip",
    },
    {
      sequence_index: 3,
      role: "button",
      accessible_name: "Submit Audit",
      description: null,
      heading_level: null,
      landmark_type: null,
      is_interactive: true,
      selector: "button.submit-btn",
      tag_name: "button",
      has_name: true,
      attributes: { type: "submit" },
      associated_finding_id: null,
      potential_issue: null,
    },
    {
      sequence_index: 4,
      role: "button",
      accessible_name: null,
      description: null,
      heading_level: null,
      landmark_type: null,
      is_interactive: true,
      selector: "button.icon-only",
      tag_name: "button",
      has_name: false,
      attributes: {},
      associated_finding_id: "finding-btn-01",
      potential_issue: "Missing accessible name",
    },
  ],
  headings: [
    {
      level: 1,
      text: "Main Platform Heading",
      sequence_index: 1,
      selector: "header > h1",
      is_skipped: false,
    },
    {
      level: 3,
      text: "Skipped Subsection",
      sequence_index: 2,
      selector: "main > h3",
      is_skipped: true,
    },
  ],
  landmarks: [
    {
      landmark_type: "banner",
      accessible_name: "AccessGuard AI Banner",
      sequence_index: 0,
      selector: "header",
    },
  ],
  interactive_elements: [
    {
      sequence_index: 3,
      role: "button",
      accessible_name: "Submit Audit",
      description: null,
      heading_level: null,
      landmark_type: null,
      is_interactive: true,
      selector: "button.submit-btn",
      tag_name: "button",
      has_name: true,
      attributes: { type: "submit" },
      associated_finding_id: null,
      potential_issue: null,
    },
    {
      sequence_index: 4,
      role: "button",
      accessible_name: null,
      description: null,
      heading_level: null,
      landmark_type: null,
      is_interactive: true,
      selector: "button.icon-only",
      tag_name: "button",
      has_name: false,
      attributes: {},
      associated_finding_id: "finding-btn-01",
      potential_issue: "Missing accessible name",
    },
  ],
  review_hints: [
    {
      category: "heading_skip",
      message: "Heading level skipped from H1 directly to H3.",
      severity: "advisory",
      sequence_index: 2,
      selector: "main > h3",
      associated_finding_id: "finding-h3-01",
    },
    {
      category: "missing_name",
      message: "Interactive control <button> lacks an accessible name.",
      severity: "warning",
      sequence_index: 4,
      selector: "button.icon-only",
      associated_finding_id: "finding-btn-01",
    },
  ],
};

const mockPages: ScanPageSummary[] = [
  {
    id: "page-test-001",
    scan_id: "scan-test-001",
    url: "https://example.com/demo",
    title: "Demo Page",
    status: "completed",
    violations_count: 2,
    has_screenshot: true,
    viewport_width: 1280,
    viewport_height: 800,
  },
];


describe("ScreenReaderSimulator Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders screen reader simulation header and enterprise disclaimer", async () => {
    vi.mocked(api.getScreenReaderSimulationApi).mockResolvedValueOnce(mockSimulationData);

    render(
      <ScreenReaderSimulator
        scanId="scan-test-001"
        pages={mockPages}
        selectedPageId="page-test-001"
        onSelectPage={vi.fn()}
      />
    );

    expect(await screen.findByText(/Screen Reader Reading & Semantics Simulator/i)).toBeInTheDocument();
    expect(screen.getByText(/Screen-Reader-Oriented Preview:/i)).toBeInTheDocument();
    expect(screen.getByText(/does not emulate real assistive technology software/i)).toBeInTheDocument();
  });

  it("navigates sequential reading order with step-through controls", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getScreenReaderSimulationApi).mockResolvedValueOnce(mockSimulationData);

    render(
      <ScreenReaderSimulator
        scanId="scan-test-001"
        pages={mockPages}
        selectedPageId="page-test-001"
        onSelectPage={vi.fn()}
      />
    );

    // Initial node is 1 (banner)
    expect(await screen.findByText(/"Banner landmark, AccessGuard AI Banner"/i)).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent?.replace(/\s+/g, " ").trim() === "Node 1 of 5")).toBeInTheDocument();

    // Step next to Node 2 (Heading 1)
    const nextBtn = screen.getByRole("button", { name: /Next ▶/i });
    await user.click(nextBtn);

    expect(screen.getByText(/"Heading level 1, Main Platform Heading"/i)).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent?.replace(/\s+/g, " ").trim() === "Node 2 of 5")).toBeInTheDocument();

    // Step next to Node 3 (Heading 3 with skip alert)
    await user.click(nextBtn);
    expect(screen.getByText(/"Heading level 3, Skipped Subsection"/i)).toBeInTheDocument();
    expect(screen.getByText(/Review Alert:/i)).toBeInTheDocument();

    // Reset back to Node 1
    const resetBtn = screen.getByRole("button", { name: /Reset/i });
    await user.click(resetBtn);
    expect(screen.getByText((_, el) => el?.textContent?.replace(/\s+/g, " ").trim() === "Node 1 of 5")).toBeInTheDocument();

  });

  it("renders headings outline with level skip indicator", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getScreenReaderSimulationApi).mockResolvedValueOnce(mockSimulationData);

    render(
      <ScreenReaderSimulator
        scanId="scan-test-001"
        pages={mockPages}
        selectedPageId="page-test-001"
        onSelectPage={vi.fn()}
      />
    );

    const headingsTab = await screen.findByRole("button", { name: /Headings Outline/i });
    await user.click(headingsTab);

    expect(screen.getByText(/Main Platform Heading/i)).toBeInTheDocument();
    expect(screen.getByText(/Skipped Subsection/i)).toBeInTheDocument();
    expect(screen.getByText(/Level Skip Alert/i)).toBeInTheDocument();
  });

  it("renders review hints and allows inspecting linked finding", async () => {
    const user = userEvent.setup();
    const onInspect = vi.fn();
    vi.mocked(api.getScreenReaderSimulationApi).mockResolvedValueOnce(mockSimulationData);

    render(
      <ScreenReaderSimulator
        scanId="scan-test-001"
        pages={mockPages}
        selectedPageId="page-test-001"
        onSelectPage={vi.fn()}
        onInspectFinding={onInspect}
      />
    );

    const hintsTab = await screen.findByRole("button", { name: /Review Hints/i });
    await user.click(hintsTab);

    expect(screen.getByText(/Heading level skipped from H1 directly to H3/i)).toBeInTheDocument();
    expect(screen.getByText(/Interactive control <button> lacks an accessible name/i)).toBeInTheDocument();

    // Click "View Finding" button on the first hint
    const viewFindingBtns = screen.getAllByRole("button", { name: /View Finding/i });
    expect(viewFindingBtns.length).toBe(2);
    await user.click(viewFindingBtns[0]);

    expect(onInspect).toHaveBeenCalledWith("finding-h3-01");
  });
});
