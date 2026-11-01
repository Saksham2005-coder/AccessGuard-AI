import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KeyboardNavigator } from '../components/keyboard/KeyboardNavigator';
import * as keyboardApi from '../api/keyboardTest';
import { ScanPageSummary } from '../api/heatmap';

const mockPages: ScanPageSummary[] = [
  {
    id: 'page-1',
    scan_id: 'scan-1',
    url: 'https://example.com/checkout',
    title: 'Checkout Flow',
    status: 'completed',
    viewport_width: 1280,
    viewport_height: 800,
    violations_count: 3,
    has_screenshot: true,
  },
];

const mockReport: keyboardApi.KeyboardNavigationReport = {
  scan_id: 'scan-1',
  page_id: 'page-1',
  page_url: 'https://example.com/checkout',
  viewport: { width: 1280, height: 800 },
  summary: {
    total_steps: 4,
    forward_steps: 3,
    reverse_steps: 1,
    unique_elements: 3,
    issues_count: 2,
    has_potential_trap: false,
    missing_indicator_count: 1,
    missing_name_count: 1,
    positive_tabindex_count: 0,
    completion_status: 'completed',
  },
  steps: [
    {
      step_index: 1,
      action: 'Tab',
      selector: '#nav-skip',
      tag_name: 'a',
      role: 'link',
      accessible_name: 'Skip to primary content',
      tabindex: 0,
      bounding_box: { x: 10, y: 10, width: 120, height: 35 },
      is_clipped_or_offscreen: false,
      has_visible_focus_indicator: true,
      focus_style: {
        outline_style: 'solid',
        outline_width: '2px',
        outline_color: 'rgb(37, 99, 235)',
        outline_offset: '2px',
        box_shadow: 'none',
        border_style: 'none',
        border_width: '0px',
        border_color: '',
      },
    },
    {
      step_index: 2,
      action: 'Tab',
      selector: '#btn-submit',
      tag_name: 'button',
      role: 'button',
      accessible_name: 'Place Order Now',
      tabindex: 0,
      bounding_box: { x: 50, y: 150, width: 180, height: 45 },
      is_clipped_or_offscreen: false,
      has_visible_focus_indicator: true,
      focus_style: {
        outline_style: 'solid',
        outline_width: '2px',
        outline_color: 'rgb(37, 99, 235)',
        outline_offset: '2px',
        box_shadow: 'none',
        border_style: 'none',
        border_width: '0px',
        border_color: '',
      },
    },
    {
      step_index: 3,
      action: 'Tab',
      selector: '#bad-icon-btn',
      tag_name: 'button',
      role: 'button',
      accessible_name: '',
      tabindex: null,
      bounding_box: { x: 250, y: 150, width: 40, height: 40 },
      is_clipped_or_offscreen: false,
      has_visible_focus_indicator: false,
      focus_style: {
        outline_style: 'none',
        outline_width: '0px',
        outline_color: '',
        outline_offset: '0px',
        box_shadow: 'none',
        border_style: 'none',
        border_width: '0px',
        border_color: '',
      },
    },
  ],
  reverse_steps: [],
  issues: [
    {
      issue_type: 'missing_accessible_name',
      severity: 'critical',
      step_index: 3,
      selector: '#bad-icon-btn',
      message: "Interactive focusable element '#bad-icon-btn' has no discernible accessible name.",
      recommendation: 'Provide an accessible label using aria-label or visible text.',
      wcag_criteria: ['4.1.2 Name, Role, Value'],
    },
    {
      issue_type: 'missing_focus_indicator',
      severity: 'serious',
      step_index: 3,
      selector: '#bad-icon-btn',
      message: "Element '#bad-icon-btn' does not present a discernible focus indicator.",
      recommendation: 'Provide a high-contrast focus ring.',
      wcag_criteria: ['2.4.7 Focus Visible'],
    },
  ],
  disclaimer:
    'Automated keyboard interaction test. Simulates standard Tab and Shift+Tab browser focus traversal.',
  tested_at: '2026-11-01T12:00:00Z',
};

describe('KeyboardNavigator Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders summary metrics and disclaimer banner', async () => {
    vi.spyOn(keyboardApi, 'getKeyboardTestApi').mockResolvedValue(mockReport);

    render(<KeyboardNavigator scanId="scan-1" pages={mockPages} />);

    await waitFor(() => {
      expect(screen.getByText(/Automated Keyboard Focus Simulation:/i)).toBeInTheDocument();
    });

    expect(screen.getByText('Focus Stops')).toBeInTheDocument();
    expect(screen.getByText('No Trap Detected')).toBeInTheDocument();
    expect(screen.getByText('Missing Focus Ring')).toBeInTheDocument();
    expect(screen.getByText('Unlabeled Controls')).toBeInTheDocument();
  });

  it('steps through the keyboard focus journey using next and previous buttons', async () => {
    vi.spyOn(keyboardApi, 'getKeyboardTestApi').mockResolvedValue(mockReport);

    render(<KeyboardNavigator scanId="scan-1" pages={mockPages} />);

    await waitFor(() => {
      expect(screen.getByText('"Skip to primary content"')).toBeInTheDocument();
    });

    // Advance to step 2
    const nextBtn = screen.getByTitle('Next Step');
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(screen.getByText('"Place Order Now"')).toBeInTheDocument();
    });

    // Advance to step 3 (unlabeled control)
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(screen.getByText(/Missing Accessible Name \(WCAG 4\.1\.2\)/i)).toBeInTheDocument();
      expect(screen.getByText(/No Discernible Focus Ring/i)).toBeInTheDocument();
    });

    // Step back to step 2
    const prevBtn = screen.getByTitle('Previous Step');
    fireEvent.click(prevBtn);

    await waitFor(() => {
      expect(screen.getByText('"Place Order Now"')).toBeInTheDocument();
    });
  });

  it('switches to Detected Issues tab and allows jumping to a step', async () => {
    vi.spyOn(keyboardApi, 'getKeyboardTestApi').mockResolvedValue(mockReport);

    render(<KeyboardNavigator scanId="scan-1" pages={mockPages} />);

    await waitFor(() => {
      expect(screen.getByText(/Detected Issues \(2\)/i)).toBeInTheDocument();
    });

    // Click Detected Issues tab
    const issuesTab = screen.getByText(/Detected Issues \(2\)/i);
    fireEvent.click(issuesTab);

    // Verify issues rendered
    expect(screen.getByText("Interactive focusable element '#bad-icon-btn' has no discernible accessible name.")).toBeInTheDocument();
    expect(screen.getByText('4.1.2 Name, Role, Value')).toBeInTheDocument();

    // Jump to step #3
    const jumpBtns = screen.getAllByText(/Jump to Step #3/i);
    fireEvent.click(jumpBtns[0]);

    // Should switch back to journey and highlight step 3
    await waitFor(() => {
      expect(screen.getByText(/Stop #3/i)).toBeInTheDocument();
      expect(screen.getAllByText('#bad-icon-btn').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('handles error state and allows retrying test', async () => {
    vi.spyOn(keyboardApi, 'getKeyboardTestApi').mockRejectedValue(new Error('Network connection dropped'));
    const rerunSpy = vi.spyOn(keyboardApi, 'rerunKeyboardTestApi').mockResolvedValue(mockReport);

    render(<KeyboardNavigator scanId="scan-1" pages={mockPages} />);

    await waitFor(() => {
      expect(screen.getByText('Network connection dropped')).toBeInTheDocument();
    });

    const retryBtn = screen.getByText('Retry Keyboard Test');
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(rerunSpy).toHaveBeenCalledWith('scan-1', 'page-1');
      expect(screen.getByText('"Skip to primary content"')).toBeInTheDocument();
    });
  });
});
