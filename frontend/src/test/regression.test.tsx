import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RegressionMonitoringModal } from '../components/regression/RegressionMonitoringModal';
import * as regressionApi from '../api/regression';
import { Scan } from '../api/scans';

const mockCurrentScan: Scan = {
  id: 'scan-curr-123',
  project_id: 'proj-123',
  requested_by: 'user-123',
  target_url: 'https://example.com/app',
  status: 'completed',
  total_pages: 5,
  pages_succeeded: 5,
  pages_failed: 0,
  total_violations: 4,
  axe_version: '4.14.0',
  browser_version: 'Chromium 128.0',
  config: { max_pages: 10 },
  created_at: '2026-11-01T12:00:00Z',
  started_at: '2026-11-01T12:00:01Z',
  completed_at: '2026-11-01T12:05:00Z',
  error_code: null,
  error_summary: null,
};

const mockAvailableScans: Scan[] = [
  mockCurrentScan,
  {
    id: 'scan-base-456',
    project_id: 'proj-123',
    requested_by: 'user-123',
    target_url: 'https://example.com/app',
    status: 'completed',
    total_pages: 5,
    pages_succeeded: 5,
    pages_failed: 0,
    total_violations: 5,
    axe_version: '4.14.0',
    browser_version: 'Chromium 128.0',
    config: { max_pages: 10 },
    created_at: '2026-10-25T12:00:00Z',
    started_at: '2026-10-25T12:00:01Z',
    completed_at: '2026-10-25T12:05:00Z',
    error_code: null,
    error_summary: null,
  },
];

const mockReport: regressionApi.RegressionComparisonReport = {
  project_id: 'proj-123',
  current_scan_id: 'scan-curr-123',
  baseline_scan_id: 'scan-base-456',
  baseline_type: 'pinned',
  current_scan_date: '2026-11-01T12:05:00Z',
  baseline_scan_date: '2026-10-25T12:05:00Z',
  coverage: {
    baseline_pages_count: 5,
    current_pages_count: 5,
    matched_pages_count: 5,
    missing_pages_count: 0,
    new_pages_count: 0,
    coverage_status: 'full',
    notes: [],
  },
  summary: {
    new_count: 1,
    resolved_count: 2,
    persistent_count: 2,
    changed_count: 1,
    inconclusive_count: 0,
    net_change: -1,
    has_critical_regression: false,
  },
  findings: [
    {
      finding_id: 'f-1',
      page_url: 'https://example.com/app/dashboard',
      axe_rule_id: 'button-name',
      impact: 'serious',
      description: 'Button has no accessible name',
      selector: 'button#submit',
      html_snippet: '<button id="submit"></button>',
      wcag_tags: ['wcag412'],
      classification: 'new',
      change_details: 'Introduced since baseline scan',
      fingerprint: 'v1:abc123456789',
    },
    {
      finding_id: 'f-2',
      page_url: 'https://example.com/app/login',
      axe_rule_id: 'image-alt',
      impact: 'critical',
      description: 'Image missing alt text',
      selector: 'img#hero',
      html_snippet: '<img id="hero">',
      wcag_tags: ['wcag111'],
      classification: 'resolved',
      change_details: 'Resolved in current audit',
      fingerprint: 'v1:def987654321',
    },
    {
      finding_id: 'f-3',
      page_url: 'https://example.com/app/settings',
      axe_rule_id: 'color-contrast',
      impact: 'moderate',
      description: 'Text contrast below threshold',
      selector: 'p.note',
      html_snippet: '<p class="note">Gray</p>',
      wcag_tags: ['wcag143'],
      classification: 'persistent',
      change_details: 'Unchanged across audits',
      fingerprint: 'v1:xyz555666777',
    },
  ],
  fingerprint_version: 'v1',
  compared_at: '2026-11-01T12:10:00Z',
};

const mockSchedules: regressionApi.ScanScheduleResponse[] = [
  {
    id: 'sched-1',
    project_id: 'proj-123',
    cadence: 'weekly',
    target_url: 'https://example.com/app',
    is_active: true,
    last_run_at: '2026-10-25T12:00:00Z',
    next_run_at: '2026-11-02T12:00:00Z',
    notify_on_regression: true,
    created_at: '2026-10-20T10:00:00Z',
  },
];

describe('RegressionMonitoringModal Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders regression report with summary metrics, net delta, and coverage status', async () => {
    vi.spyOn(regressionApi, 'getProjectBaselineApi').mockResolvedValue(null);
    vi.spyOn(regressionApi, 'compareScanRegressionApi').mockResolvedValue(mockReport);
    vi.spyOn(regressionApi, 'listScanSchedulesApi').mockResolvedValue(mockSchedules);

    render(
      <RegressionMonitoringModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        currentScan={mockCurrentScan}
        availableScans={mockAvailableScans}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Coverage-Aware Historical Regression Analysis:/i)).toBeInTheDocument();
    });

    expect(screen.getByText('Net Delta')).toBeInTheDocument();
    expect(screen.getByText('-1')).toBeInTheDocument();
    expect(screen.getByText('New Regressions')).toBeInTheDocument();
    expect(screen.getByText('Resolved Issues')).toBeInTheDocument();
    expect(screen.getByText(/Full surface match: All 5 pages match baseline coverage/i)).toBeInTheDocument();
  });

  it('filters findings when clicking classification tabs', async () => {
    vi.spyOn(regressionApi, 'getProjectBaselineApi').mockResolvedValue(null);
    vi.spyOn(regressionApi, 'compareScanRegressionApi').mockResolvedValue(mockReport);
    vi.spyOn(regressionApi, 'listScanSchedulesApi').mockResolvedValue(mockSchedules);

    render(
      <RegressionMonitoringModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        currentScan={mockCurrentScan}
        availableScans={mockAvailableScans}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('button#submit')).toBeInTheDocument();
      expect(screen.getByText('img#hero')).toBeInTheDocument();
    });

    // Filter by new regressions
    const newTab = screen.getByText('new (1)');
    fireEvent.click(newTab);

    expect(screen.getByText('button#submit')).toBeInTheDocument();
    expect(screen.queryByText('img#hero')).not.toBeInTheDocument();

    // Filter by resolved
    const resolvedTab = screen.getByText('resolved (1)');
    fireEvent.click(resolvedTab);

    expect(screen.getByText('img#hero')).toBeInTheDocument();
    expect(screen.queryByText('button#submit')).not.toBeInTheDocument();
  });

  it('switches to Scheduled Audits tab and displays existing schedules', async () => {
    vi.spyOn(regressionApi, 'getProjectBaselineApi').mockResolvedValue(null);
    vi.spyOn(regressionApi, 'compareScanRegressionApi').mockResolvedValue(mockReport);
    vi.spyOn(regressionApi, 'listScanSchedulesApi').mockResolvedValue(mockSchedules);

    render(
      <RegressionMonitoringModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        currentScan={mockCurrentScan}
        availableScans={mockAvailableScans}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Scheduled Audits \(1\)/i)).toBeInTheDocument();
    });

    const schedulesTab = screen.getByText(/Scheduled Audits \(1\)/i);
    fireEvent.click(schedulesTab);

    expect(screen.getByText('weekly Audit')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/app')).toBeInTheDocument();
    expect(screen.getByText('Create Schedule')).toBeInTheDocument();
  });

  it('allows pinning current scan as project baseline', async () => {
    vi.spyOn(regressionApi, 'getProjectBaselineApi').mockResolvedValue(null);
    vi.spyOn(regressionApi, 'compareScanRegressionApi').mockResolvedValue(mockReport);
    vi.spyOn(regressionApi, 'listScanSchedulesApi').mockResolvedValue(mockSchedules);
    const pinSpy = vi.spyOn(regressionApi, 'setProjectBaselineApi').mockResolvedValue({
      id: 'base-pin-1',
      project_id: 'proj-123',
      scan_id: mockCurrentScan.id,
      scan_date: '2026-11-01T12:00:00Z',
      scan_target_url: mockCurrentScan.target_url,
      pinned_at: '2026-11-01T12:15:00Z',
      notes: 'v2 release baseline',
    });

    render(
      <RegressionMonitoringModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        currentScan={mockCurrentScan}
        availableScans={mockAvailableScans}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Pin This Scan as Baseline')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Pin This Scan as Baseline'));

    expect(screen.getByText('Pin Current Scan as Project Baseline')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Optional baseline description/i);
    fireEvent.change(input, { target: { value: 'v2 release baseline' } });

    fireEvent.click(screen.getByText('Confirm Baseline Pin'));

    await waitFor(() => {
      expect(pinSpy).toHaveBeenCalledWith('proj-123', mockCurrentScan.id, 'v2 release baseline');
    });
  });
});
