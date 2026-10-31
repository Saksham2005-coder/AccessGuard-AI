import { apiClient } from "./client";

export interface ScanConfig {
  max_pages?: number;
  max_depth?: number;
  [key: string]: unknown;
}

export interface Scan {
  id: string;
  project_id: string;
  requested_by: string;
  target_url: string;
  status:
    | "pending"
    | "running"
    | "crawling"
    | "auditing"
    | "completed"
    | "completed_with_errors"
    | "failed"
    | "cancelled"
    | string;
  config: ScanConfig;
  started_at: string | null;
  completed_at: string | null;
  total_pages: number;
  pages_succeeded: number;
  pages_failed: number;
  total_violations: number;
  axe_version: string | null;
  browser_version: string | null;
  error_code: string | null;
  error_summary: string | null;
  created_at: string;
}

export interface ScanListResponse {
  items: Scan[];
  total: number;
}

export interface ScanCreateRequest {
  target_url: string;
  max_pages?: number;
  max_depth?: number;
}

export interface ScanEventItem {
  sequence_number: number;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export async function createScanApi(
  projectId: string,
  payload: ScanCreateRequest
): Promise<Scan> {
  const response = await apiClient.post<Scan>(
    `/projects/${projectId}/scans`,
    payload
  );
  return response.data;
}

export async function listProjectScansApi(
  projectId: string
): Promise<ScanListResponse> {
  const response = await apiClient.get<ScanListResponse>(
    `/projects/${projectId}/scans`
  );
  return response.data;
}

export async function getScanApi(scanId: string): Promise<Scan> {
  const response = await apiClient.get<Scan>(`/scans/${scanId}`);
  return response.data;
}

export async function cancelScanApi(scanId: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>(
    `/scans/${scanId}/cancel`
  );
  return response.data;
}
