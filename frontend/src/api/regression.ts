/**
 * API client for Accessibility Regression Monitoring.
 * Phase 19 Feature 6: Historical regression analysis, pinned baselines,
 * scheduled audits, and in-app notifications.
 */

import { apiClient } from './client';

export interface RegressionFindingItem {
  finding_id: string;
  page_url: string;
  axe_rule_id: string;
  impact: string | null;
  description: string;
  selector: string | null;
  html_snippet: string | null;
  wcag_tags: string[];
  classification: 'new' | 'resolved' | 'persistent' | 'changed' | 'inconclusive';
  change_details: string | null;
  fingerprint: string;
}

export interface CoverageSummary {
  baseline_pages_count: number;
  current_pages_count: number;
  matched_pages_count: number;
  missing_pages_count: number;
  new_pages_count: number;
  coverage_status: 'full' | 'partial' | 'inconclusive';
  notes: string[];
}

export interface RegressionComparisonSummary {
  new_count: number;
  resolved_count: number;
  persistent_count: number;
  changed_count: number;
  inconclusive_count: number;
  net_change: number;
  has_critical_regression: boolean;
}

export interface RegressionComparisonReport {
  project_id: string;
  current_scan_id: string;
  baseline_scan_id: string;
  baseline_type: 'pinned' | 'previous_successful' | 'custom_selection';
  current_scan_date: string;
  baseline_scan_date: string;
  coverage: CoverageSummary;
  summary: RegressionComparisonSummary;
  findings: RegressionFindingItem[];
  fingerprint_version: string;
  compared_at: string;
}

export interface ProjectBaselineResponse {
  id: string;
  project_id: string;
  scan_id: string;
  scan_date: string;
  scan_target_url: string;
  pinned_at: string;
  notes: string | null;
}

export interface ScanScheduleResponse {
  id: string;
  project_id: string;
  cadence: string;
  target_url: string;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  notify_on_regression: boolean;
  created_at: string;
}

export interface InAppNotificationResponse {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  link_url: string | null;
  is_read: boolean;
  created_at: string;
}

export async function compareScanRegressionApi(
  projectId: string,
  currentScanId: string,
  baselineScanId?: string
): Promise<RegressionComparisonReport> {
  const response = await apiClient.get<RegressionComparisonReport>(
    `/projects/${projectId}/regression/compare`,
    {
      params: {
        current_scan_id: currentScanId,
        baseline_scan_id: baselineScanId,
      },
    }
  );
  return response.data;
}

export async function getProjectBaselineApi(
  projectId: string
): Promise<ProjectBaselineResponse | null> {
  const response = await apiClient.get<ProjectBaselineResponse | null>(
    `/projects/${projectId}/baseline`
  );
  return response.data;
}

export async function setProjectBaselineApi(
  projectId: string,
  scanId: string,
  notes?: string
): Promise<ProjectBaselineResponse> {
  const response = await apiClient.post<ProjectBaselineResponse>(
    `/projects/${projectId}/baseline`,
    {
      scan_id: scanId,
      notes,
    }
  );
  return response.data;
}

export async function listScanSchedulesApi(
  projectId: string
): Promise<ScanScheduleResponse[]> {
  const response = await apiClient.get<ScanScheduleResponse[]>(
    `/projects/${projectId}/schedules`
  );
  return response.data;
}

export async function createScanScheduleApi(
  projectId: string,
  payload: { cadence: string; target_url: string; notify_on_regression?: boolean }
): Promise<ScanScheduleResponse> {
  const response = await apiClient.post<ScanScheduleResponse>(
    `/projects/${projectId}/schedules`,
    payload
  );
  return response.data;
}

export async function toggleScanScheduleApi(
  projectId: string,
  scheduleId: string,
  isActive: boolean
): Promise<ScanScheduleResponse> {
  const response = await apiClient.patch<ScanScheduleResponse>(
    `/projects/${projectId}/schedules/${scheduleId}`,
    null,
    {
      params: { is_active: isActive },
    }
  );
  return response.data;
}

export async function deleteScanScheduleApi(
  projectId: string,
  scheduleId: string
): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/schedules/${scheduleId}`);
}

export async function getNotificationsApi(
  unreadOnly = false
): Promise<InAppNotificationResponse[]> {
  const response = await apiClient.get<InAppNotificationResponse[]>(
    '/notifications',
    {
      params: { unread_only: unreadOnly },
    }
  );
  return response.data;
}

export async function markNotificationReadApi(
  notificationId: string
): Promise<void> {
  await apiClient.patch(`/notifications/${notificationId}/read`);
}
