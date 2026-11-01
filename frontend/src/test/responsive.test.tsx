import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResponsiveMatrixModal } from '../components/responsive/ResponsiveMatrixModal';
import * as responsiveApi from '../api/responsive';

const mockReport: responsiveApi.ResponsiveMatrixReport = {
  scan_id: 'scan-123',
  target_url: 'https://example.com/portal',
  viewport_runs: [
    {
      id: 'run-desktop',
      scan_id: 'scan-123',
      viewport_name: 'desktop',
      width: 1440,
      height: 900,
      device_scale_factor: 1.0,
      is_mobile: false,
      violations_count: 3,
      critical_count: 1,
      serious_count: 1,
      moderate_count: 1,
      minor_count: 0,
      created_at: '2026-11-01T12:00:00Z',
    },
    {
      id: 'run-tablet',
      scan_id: 'scan-123',
      viewport_name: 'tablet',
      width: 768,
      height: 1024,
      device_scale_factor: 2.0,
      is_mobile: false,
      violations_count: 4,
      critical_count: 1,
      serious_count: 2,
      moderate_count: 1,
      minor_count: 0,
      created_at: '2026-11-01T12:00:00Z',
    },
    {
      id: 'run-mobile',
      scan_id: 'scan-123',
      viewport_name: 'mobile',
      width: 390,
      height: 844,
      device_scale_factor: 3.0,
      is_mobile: true,
      violations_count: 5,
      critical_count: 1,
      serious_count: 3,
      moderate_count: 1,
      minor_count: 0,
      created_at: '2026-11-01T12:00:00Z',
    },
  ],
  shared_findings: [
    {
      rule_id: 'color-contrast',
      impact: 'serious',
      selector: 'h1.main-title',
      description: 'Text element has insufficient contrast ratio of 2.8:1',
      viewports_affected: ['desktop', 'tablet', 'mobile'],
      is_shared_across_all: true,
    },
  ],
  viewport_specific_findings: [
    {
      rule_id: 'target-size',
      impact: 'serious',
      selector: 'button.hamburger-menu',
      description: 'Touch target size is 28x28px, failing WCAG 2.5.8 minimum 24x24px / 48x48px',
      viewports_affected: ['mobile'],
      is_shared_across_all: false,
    },
    {
      rule_id: 'reflow',
      impact: 'moderate',
      selector: 'table.data-grid',
      description: 'Horizontal scrolling required at 320px equivalent width',
      viewports_affected: ['tablet', 'mobile'],
      is_shared_across_all: false,
    },
  ],
  total_unique_rules: 3,
  total_cross_viewport_violations: 12,
};

describe('ResponsiveMatrixModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders viewport cards and shared vs specific findings', async () => {
    vi.spyOn(responsiveApi, 'getResponsiveMatrix').mockResolvedValue(mockReport);

    render(
      <ResponsiveMatrixModal
        isOpen={true}
        onClose={vi.fn()}
        scanId="scan-123"
        targetUrl="https://example.com/portal"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Multi-Viewport Accessibility Matrix')).toBeDefined();
    });

    expect(screen.getByText('https://example.com/portal')).toBeDefined();
    expect(screen.getByTestId('viewport-card-desktop')).toBeDefined();
    expect(screen.getByTestId('viewport-card-tablet')).toBeDefined();
    expect(screen.getByTestId('viewport-card-mobile')).toBeDefined();

    // Verify findings are displayed
    expect(screen.getByText('color-contrast')).toBeDefined();
    expect(screen.getByText('target-size')).toBeDefined();
    expect(screen.getByText('reflow')).toBeDefined();
    expect(screen.getByText('WCAG 2.5.8 Touch Target')).toBeDefined();
  });

  it('filters by viewport when a profile card is clicked', async () => {
    vi.spyOn(responsiveApi, 'getResponsiveMatrix').mockResolvedValue(mockReport);

    render(
      <ResponsiveMatrixModal
        isOpen={true}
        onClose={vi.fn()}
        scanId="scan-123"
        targetUrl="https://example.com/portal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('viewport-card-mobile')).toBeDefined();
    });

    // Click mobile card to filter
    fireEvent.click(screen.getByTestId('viewport-card-mobile'));

    expect(screen.getByText('Clear Filter (mobile)')).toBeDefined();
    // In mobile, target-size and reflow are both affected
    expect(screen.getByText('target-size')).toBeDefined();

    // Clear filter
    fireEvent.click(screen.getByText('Clear Filter (mobile)'));
    expect(screen.queryByText('Clear Filter (mobile)')).toBeNull();
  });

  it('re-evaluates matrix on recompute button click', async () => {
    vi.spyOn(responsiveApi, 'getResponsiveMatrix').mockResolvedValue(mockReport);
    const runSpy = vi.spyOn(responsiveApi, 'runResponsiveMatrix').mockResolvedValue({
      ...mockReport,
      total_cross_viewport_violations: 14,
    });

    render(
      <ResponsiveMatrixModal
        isOpen={true}
        onClose={vi.fn()}
        scanId="scan-123"
        targetUrl="https://example.com/portal"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('recompute-matrix-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('recompute-matrix-btn'));

    await waitFor(() => {
      expect(runSpy).toHaveBeenCalledWith('scan-123', { force_recompute: true });
    });
  });

  it('handles error state gracefully', async () => {
    vi.spyOn(responsiveApi, 'getResponsiveMatrix').mockRejectedValue(
      new Error('Failed to connect to scan worker')
    );

    render(
      <ResponsiveMatrixModal
        isOpen={true}
        onClose={vi.fn()}
        scanId="scan-123"
        targetUrl="https://example.com/portal"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Error loading responsive matrix')).toBeDefined();
      expect(screen.getByText('Failed to connect to scan worker')).toBeDefined();
    });
  });
});
