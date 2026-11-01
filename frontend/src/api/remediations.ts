import { apiClient } from "./client";

export interface RemediationApproval {
  id: string;
  remediation_id: string;
  reviewer_id: string;
  decision: "approved" | "rejected" | string;
  comments: string | null;
  created_at: string;
}

export interface ValidationResult {
  id: string;
  remediation_id: string;
  validation_mode: string;
  passed: boolean;
  original_rule_resolved: boolean;
  new_violations: Array<Record<string, unknown>>;
  details: Record<string, unknown>;
  created_at: string;
}

export interface Remediation {
  id: string;
  finding_id: string;
  status:
    | "pending_approval"
    | "approved"
    | "rejected"
    | "validated"
    | "validation_failed"
    | string;
  root_cause: string;
  recommendation: string;
  patch_format: string;
  patch_payload: Record<string, unknown>;
  before_snippet: string | null;
  after_snippet: string | null;
  confidence: number | null;
  model_provider: string | null;
  model_name: string | null;
  prompt_version: string | null;
  approvals: RemediationApproval[];
  validation_results: ValidationResult[];
  created_at: string;
  updated_at: string;
}

export interface ListRemediationsParams {
  finding_id?: string;
  status_filter?: string;
}

export async function listRemediationsApi(
  params?: ListRemediationsParams
): Promise<Remediation[]> {
  const response = await apiClient.get<Remediation[]>("/remediations", {
    params,
  });
  return response.data;
}

export async function generateRemediationApi(
  findingId: string
): Promise<Remediation> {
  const response = await apiClient.post<Remediation>(
    `/findings/${findingId}/remediations`
  );
  return response.data;
}

export async function getRemediationApi(
  remediationId: string
): Promise<Remediation> {
  const response = await apiClient.get<Remediation>(
    `/remediations/${remediationId}`
  );
  return response.data;
}

export async function approveRemediationApi(
  remediationId: string,
  comments?: string
): Promise<Remediation> {
  const response = await apiClient.post<Remediation>(
    `/remediations/${remediationId}/approve`,
    {
      decision: "approved",
      comments: comments || null,
    }
  );
  return response.data;
}

export async function rejectRemediationApi(
  remediationId: string,
  comments?: string
): Promise<Remediation> {
  const response = await apiClient.post<Remediation>(
    `/remediations/${remediationId}/reject`,
    {
      decision: "rejected",
      comments: comments || null,
    }
  );
  return response.data;
}

export async function validateRemediationApi(
  remediationId: string
): Promise<Remediation> {
  const response = await apiClient.post<Remediation>(
    `/remediations/${remediationId}/validate`
  );
  return response.data;
}

export async function getValidationHistoryApi(
  remediationId: string
): Promise<ValidationResult[]> {
  const response = await apiClient.get<ValidationResult[]>(
    `/remediations/${remediationId}/validation`
  );
  return response.data;
}

export interface ComparisonResponse {
  remediation_id: string;
  finding_id: string;
  rule_id: string;
  before_html: string;
  after_html: string;
  before_screenshot_url: string | null;
  after_screenshot_url: string | null;
  dom_diff: string;
  patch_operations: Array<Record<string, unknown>>;
  original_rule_resolved: boolean;
  new_violations: Array<{
    rule_id: string;
    impact: string;
    description: string;
    primary_selector?: string;
  }>;
  passed: boolean;
  status: string;
  created_at: string;
  details: Record<string, unknown>;
}

export async function runRemediationComparisonApi(
  remediationId: string
): Promise<ComparisonResponse> {
  const response = await apiClient.post<ComparisonResponse>(
    `/remediations/${remediationId}/compare`
  );
  return response.data;
}

export async function getRemediationComparisonApi(
  remediationId: string
): Promise<ComparisonResponse> {
  const response = await apiClient.get<ComparisonResponse>(
    `/remediations/${remediationId}/comparison`
  );
  return response.data;
}

