import { apiClient } from "./client";

export interface FindingNode {
  id: string;
  target: string[];
  html_snippet: string | null;
  failure_summary: string | null;
  screenshot_reference: string | null;
}

export interface Finding {
  id: string;
  scan_page_id: string;
  axe_rule_id: string;
  impact: "minor" | "moderate" | "serious" | "critical" | string | null;
  description: string;
  help: string | null;
  help_url: string | null;
  wcag_tags: string[];
  selector: string | null;
  html_snippet: string | null;
  failure_summary: string | null;
  fingerprint: string;
  is_incomplete: boolean;
  created_at: string;
  updated_at: string;
}

export interface FindingDetail extends Finding {
  nodes: FindingNode[];
}

export interface FindingListResponse {
  items: Finding[];
  total: number;
}

export interface ListFindingsParams {
  project_id?: string;
  scan_id?: string;
  impact?: string;
  axe_rule_id?: string;
}

export async function listFindingsApi(
  params?: ListFindingsParams
): Promise<FindingListResponse> {
  const response = await apiClient.get<FindingListResponse>("/findings", {
    params,
  });
  return response.data;
}

export async function getFindingApi(findingId: string): Promise<FindingDetail> {
  const response = await apiClient.get<FindingDetail>(`/findings/${findingId}`);
  return response.data;
}

export async function listScanFindingsApi(
  scanId: string
): Promise<FindingListResponse> {
  const response = await apiClient.get<FindingListResponse>(
    `/scans/${scanId}/findings`
  );
  return response.data;
}
