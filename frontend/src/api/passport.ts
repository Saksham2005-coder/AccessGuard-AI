/**
 * API client for Accessibility Compliance Passport.
 * Phase 19 Feature 10: Versioned, tamper-evident audit evidence package with deterministic
 * SHA-256 integrity hash, multi-engine telemetry breakdown, and audit traceability.
 */

import { apiClient } from './client';

export interface CompliancePassportSummary {
  id: string;
  project_id: string;
  version: string;
  status: string;
  integrity_hash: string;
  status_label: string;
  total_scans_included: number;
  total_violations: number;
  created_at: string;
}

export interface WcagCriterionAudited {
  criterion_id: string;
  title: string;
  level: string;
  status: string;
}

export interface ManualReviewChecklistItem {
  item: string;
  guideline: string;
  status: string;
  notes: string;
}

export interface PassportEvidencePayload {
  schema_version: string;
  passport_metadata: {
    project_id: string;
    project_name: string;
    base_domain: string;
    version: string;
    generation_timestamp: string;
    generated_by: string;
    notes?: string;
  };
  audit_scope: {
    total_scans_included: number;
    total_pages_audited: number;
    scanner_engine: string;
    axe_version: string;
  };
  compliance_evaluation: {
    status_label: string;
    total_violations: number;
    severity_breakdown: {
      critical: number;
      serious: number;
      moderate: number;
      minor: number;
    };
    unique_wcag_rules_flagged: string[];
    remediations_summary: {
      total_proposals: number;
      resolved_or_verified: number;
      pending_or_proposed: number;
    };
  };
  multi_engine_evidence: {
    multi_viewport_testing: {
      runs_recorded: number;
      viewports_tested: string[];
    };
    regression_monitoring: {
      baseline_pinned: boolean;
      baseline_scan_id?: string | null;
    };
    keyboard_simulator: {
      status: string;
    };
    screen_reader_preview: {
      status: string;
    };
  };
  wcag_criteria_audited: WcagCriterionAudited[];
  manual_review_checklist: ManualReviewChecklistItem[];
  legal_disclaimer: string;
}

export interface CompliancePassportDetail {
  id: string;
  project_id: string;
  version: string;
  status: string;
  integrity_hash: string;
  evidence_payload: PassportEvidencePayload;
  created_by?: string | null;
  created_at: string;
}

export interface GeneratePassportRequest {
  notes?: string;
}

export interface PassportExportDocument {
  passport_id: string;
  version: string;
  integrity_hash: string;
  markdown_content: string;
  generated_at: string;
}

export async function listProjectPassports(projectId: string): Promise<CompliancePassportSummary[]> {
  const response = await apiClient.get<CompliancePassportSummary[]>(`/projects/${projectId}/passports`);
  return response.data;
}

export async function getProjectPassport(
  projectId: string,
  passportId: string
): Promise<CompliancePassportDetail> {
  const response = await apiClient.get<CompliancePassportDetail>(
    `/projects/${projectId}/passports/${passportId}`
  );
  return response.data;
}

export async function generateProjectPassport(
  projectId: string,
  data?: GeneratePassportRequest
): Promise<CompliancePassportDetail> {
  const response = await apiClient.post<CompliancePassportDetail>(
    `/projects/${projectId}/passports/generate`,
    data || {}
  );
  return response.data;
}

export async function exportProjectPassportDocument(
  projectId: string,
  passportId: string
): Promise<PassportExportDocument> {
  const response = await apiClient.get<PassportExportDocument>(
    `/projects/${projectId}/passports/${passportId}/export`
  );
  return response.data;
}
