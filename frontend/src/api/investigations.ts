import { apiClient } from "./client";


export type ConfidenceLevel = "supported" | "tentative" | "insufficient_evidence";
export type InvestigationStatus = "completed" | "partial" | "skipped" | "failed";
export type PriorityLevel = "P1" | "P2" | "P3" | "P4";

export interface Observation {
  finding_id: string | null;
  rule_id: string;
  selector: string | null;
  summary: string;
  details: string | null;
  severity: string | null;
}

export interface Recommendation {
  title: string;
  action: string;
  code_example: string | null;
  priority: PriorityLevel;
  affected_finding_ids: string[];
}

export interface SpecialistReport {
  agent_id: string;
  agent_name: string;
  agent_version: string;
  dimension: string;
  status: InvestigationStatus;
  confidence: ConfidenceLevel;
  findings_count: number;
  observations: Observation[];
  recommendations: Recommendation[];
  wcag_criteria: string[];
  limitations: string[];
  evidence_references: string[];
}

export interface WcagCitation {
  criterion_id: string;
  title: string;
  level: string;
  summary: string;
  url: string | null;
}

export interface RemediationMatrixItem {
  priority: PriorityLevel;
  title: string;
  description: string;
  dimension: string;
  affected_findings: string[];
  remediation_hint: string;
}

export interface InvestigationReport {
  investigation_id: string;
  scan_id: string;
  status: InvestigationStatus;
  overall_confidence: ConfidenceLevel;
  executive_summary: string;
  specialists: Record<string, SpecialistReport>;
  remediation_matrix: RemediationMatrixItem[];
  manual_verification_checklist: string[];
  wcag_citations: WcagCitation[];
  duration_ms: number | null;
  created_at: string;
}

export interface InvestigationRunSummary {
  id: string;
  scan_id: string;
  status: string;
  overall_confidence: string;
  executive_summary: string;
  created_at: string;
}

export interface InvestigationListResponse {
  items: InvestigationRunSummary[];
  total: number;
}


export async function triggerInvestigation(
  scanId: string,
  forceRefresh = false
): Promise<InvestigationReport> {
  const response = await apiClient.post<InvestigationReport>(
    `/scans/${scanId}/investigations`,
    { force_refresh: forceRefresh }
  );
  return response.data;
}

export async function getLatestInvestigation(
  scanId: string
): Promise<InvestigationReport> {
  const response = await apiClient.get<InvestigationReport>(
    `/scans/${scanId}/investigations/latest`
  );
  return response.data;
}

export async function listInvestigations(
  scanId: string
): Promise<InvestigationListResponse> {
  const response = await apiClient.get<InvestigationListResponse>(
    `/scans/${scanId}/investigations`
  );
  return response.data;
}

export async function getInvestigationById(
  scanId: string,
  investigationId: string
): Promise<InvestigationReport> {
  const response = await apiClient.get<InvestigationReport>(
    `/scans/${scanId}/investigations/${investigationId}`
  );
  return response.data;
}
