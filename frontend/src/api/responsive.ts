/**
 * API client for Responsive Multi-Viewport Accessibility Testing.
 * Phase 19 Feature 9: Multi-viewport audit matrix, shared vs viewport-specific violation diffing.
 */

import { apiClient } from './client';

export interface ViewportProfile {
  name: string;
  width: number;
  height: number;
  device_scale_factor: number;
  is_mobile: boolean;
  has_touch: boolean;
}

export interface ViewportFindingDiff {
  rule_id: string;
  impact: string;
  selector: string;
  description: string;
  viewports_affected: string[];
  is_shared_across_all: boolean;
}

export interface ViewportRunSummary {
  id: string;
  scan_id: string;
  viewport_name: string;
  width: number;
  height: number;
  device_scale_factor: number;
  is_mobile: boolean;
  violations_count: number;
  critical_count: number;
  serious_count: number;
  moderate_count: number;
  minor_count: number;
  created_at: string;
}

export interface ResponsiveMatrixReport {
  scan_id: string;
  target_url: string;
  viewport_runs: ViewportRunSummary[];
  shared_findings: ViewportFindingDiff[];
  viewport_specific_findings: ViewportFindingDiff[];
  total_unique_rules: number;
  total_cross_viewport_violations: number;
}

export interface RunResponsiveMatrixRequest {
  profiles?: ViewportProfile[];
  force_recompute?: boolean;
}

export async function getResponsiveMatrix(scanId: string): Promise<ResponsiveMatrixReport> {
  const response = await apiClient.get<ResponsiveMatrixReport>(`/scans/${scanId}/responsive-matrix`);
  return response.data;
}

export async function runResponsiveMatrix(
  scanId: string,
  data?: RunResponsiveMatrixRequest
): Promise<ResponsiveMatrixReport> {
  const response = await apiClient.post<ResponsiveMatrixReport>(
    `/scans/${scanId}/responsive-matrix/run`,
    data || {}
  );
  return response.data;
}
