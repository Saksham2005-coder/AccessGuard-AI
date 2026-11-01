import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CompliancePassportModal } from '../components/passport/CompliancePassportModal';
import * as passportApi from '../api/passport';

const mockDetail: passportApi.CompliancePassportDetail = {
  id: 'pass-123',
  project_id: 'proj-123',
  version: 'v1',
  status: 'completed',
  integrity_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  evidence_payload: {
    schema_version: '1.0.0',
    passport_metadata: {
      project_id: 'proj-123',
      project_name: 'Production Portal',
      base_domain: 'portal.example.com',
      version: 'v1',
      generation_timestamp: '2026-11-01T12:00:00Z',
      generated_by: 'user-123',
      notes: 'Initial audit passport',
    },
    audit_scope: {
      total_scans_included: 2,
      total_pages_audited: 8,
      scanner_engine: 'axe-core with Playwright Chromium',
      axe_version: '4.14.0',
    },
    compliance_evaluation: {
      status_label: 'Outstanding automated findings',
      total_violations: 4,
      severity_breakdown: {
        critical: 1,
        serious: 2,
        moderate: 1,
        minor: 0,
      },
      unique_wcag_rules_flagged: ['color-contrast', 'button-name'],
      remediations_summary: {
        total_proposals: 2,
        resolved_or_verified: 1,
        pending_or_proposed: 1,
      },
    },
    multi_engine_evidence: {
      multi_viewport_testing: {
        runs_recorded: 3,
        viewports_tested: ['desktop', 'tablet', 'mobile'],
      },
      regression_monitoring: {
        baseline_pinned: true,
        baseline_scan_id: 'scan-base-123',
      },
      keyboard_simulator: {
        status: 'Deterministic browser navigation trace available',
      },
      screen_reader_preview: {
        status: 'Semantic accessibility tree reading preview available',
      },
    },
    wcag_criteria_audited: [
      {
        criterion_id: '1.4.3',
        title: 'Contrast (Minimum)',
        level: 'AA',
        status: 'Evaluated by axe-core',
      },
      {
        criterion_id: '2.1.1',
        title: 'Keyboard',
        level: 'A',
        status: 'Evaluated by simulator',
      },
    ],
    manual_review_checklist: [
      {
        item: 'Captions and Audio Descriptions',
        guideline: 'WCAG 1.2.2',
        status: 'Manual Review Required',
        notes: 'Check video media for accurate captions.',
      },
    ],
    legal_disclaimer:
      'This compliance passport is an auditable record of automated testing and engineering evidence. It is not an official WCAG legal certification or guarantee of non-liability.',
  },
  created_at: '2026-11-01T12:00:00Z',
};

describe('CompliancePassportModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders compliance passport modal with SHA-256 hash, non-certification notice, and evaluation status', async () => {
    vi.spyOn(passportApi, 'listProjectPassports').mockResolvedValue([
      {
        id: 'pass-123',
        project_id: 'proj-123',
        version: 'v1',
        status: 'completed',
        integrity_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        status_label: 'Outstanding automated findings',
        total_scans_included: 2,
        total_violations: 4,
        created_at: '2026-11-01T12:00:00Z',
      },
    ]);
    vi.spyOn(passportApi, 'getProjectPassport').mockResolvedValue(mockDetail);

    render(
      <CompliancePassportModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        projectName="Production Portal"
        baseDomain="portal.example.com"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Accessibility Compliance Passport')).toBeDefined();
    });

    // Check non-certification notice is visible
    expect(screen.getByText(/not an official wcag legal certification/i)).toBeDefined();

    // Check integrity hash is displayed
    expect(
      screen.getByText('9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08')
    ).toBeDefined();

    // Check status badge
    expect(screen.getByText('Outstanding automated findings')).toBeDefined();
  });

  it('switches tabs to inspect multi-engine telemetry and WCAG criteria', async () => {
    vi.spyOn(passportApi, 'listProjectPassports').mockResolvedValue([
      {
        id: 'pass-123',
        project_id: 'proj-123',
        version: 'v1',
        status: 'completed',
        integrity_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        status_label: 'Outstanding automated findings',
        total_scans_included: 2,
        total_violations: 4,
        created_at: '2026-11-01T12:00:00Z',
      },
    ]);
    vi.spyOn(passportApi, 'getProjectPassport').mockResolvedValue(mockDetail);

    render(
      <CompliancePassportModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        projectName="Production Portal"
        baseDomain="portal.example.com"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Multi-Engine Telemetry')).toBeDefined();
    });

    // Switch to Multi-Engine Telemetry
    fireEvent.click(screen.getByText('Multi-Engine Telemetry'));
    expect(screen.getByText('Responsive Multi-Viewport Matrix')).toBeDefined();
    expect(screen.getByText('Keyboard Navigation Simulator')).toBeDefined();
    expect(screen.getByText('Screen Reader Semantic Preview')).toBeDefined();

    // Switch to WCAG Criteria
    fireEvent.click(screen.getByText(/WCAG 2.2 Criteria/i));
    expect(screen.getByText('Contrast (Minimum)')).toBeDefined();

    // Switch to Manual Review Checklist
    fireEvent.click(screen.getByText('Manual Review Checklist'));
    expect(screen.getByText('Captions and Audio Descriptions')).toBeDefined();
  });

  it('generates a new version when user clicks generate button', async () => {
    vi.spyOn(passportApi, 'listProjectPassports').mockResolvedValue([
      {
        id: 'pass-123',
        project_id: 'proj-123',
        version: 'v1',
        status: 'completed',
        integrity_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        status_label: 'Outstanding automated findings',
        total_scans_included: 2,
        total_violations: 4,
        created_at: '2026-11-01T12:00:00Z',
      },
    ]);
    vi.spyOn(passportApi, 'getProjectPassport').mockResolvedValue(mockDetail);
    const genSpy = vi.spyOn(passportApi, 'generateProjectPassport').mockResolvedValue({
      ...mockDetail,
      id: 'pass-124',
      version: 'v2',
    });

    render(
      <CompliancePassportModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        projectName="Production Portal"
        baseDomain="portal.example.com"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('generate-passport-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('generate-passport-btn'));

    await waitFor(() => {
      expect(genSpy).toHaveBeenCalledWith('proj-123');
    });
  });

  it('exports JSON evidence bundle when download button is clicked', async () => {
    vi.spyOn(passportApi, 'listProjectPassports').mockResolvedValue([
      {
        id: 'pass-123',
        project_id: 'proj-123',
        version: 'v1',
        status: 'completed',
        integrity_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        status_label: 'Outstanding automated findings',
        total_scans_included: 2,
        total_violations: 4,
        created_at: '2026-11-01T12:00:00Z',
      },
    ]);
    vi.spyOn(passportApi, 'getProjectPassport').mockResolvedValue(mockDetail);

    // Mock createObjectURL & revokeObjectURL
    const createObjectUrlMock = vi.fn().mockReturnValue('blob:http://localhost/test-blob');
    const revokeObjectUrlMock = vi.fn();
    window.URL.createObjectURL = createObjectUrlMock;
    window.URL.revokeObjectURL = revokeObjectUrlMock;

    render(
      <CompliancePassportModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-123"
        projectName="Production Portal"
        baseDomain="portal.example.com"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('download-passport-json-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('download-passport-json-btn'));

    expect(createObjectUrlMock).toHaveBeenCalled();
  });
});
