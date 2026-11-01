/**
 * API client for Keyboard Navigation Simulator.
 * Phase 19 Feature 5: Deterministic keyboard-only navigation testing and focus order inspection.
 */

import { apiClient } from './client';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ComputedFocusStyle {
  outline_style: string;
  outline_width: string;
  outline_color: string;
  outline_offset: string;
  box_shadow: string;
  border_style: string;
  border_width: string;
  border_color: string;
}

export interface KeyboardStep {
  step_index: number;
  action: string;
  selector: string;
  tag_name: string;
  role?: string | null;
  accessible_name?: string | null;
  tabindex?: number | null;
  bounding_box?: BoundingBox | null;
  is_clipped_or_offscreen: boolean;
  has_visible_focus_indicator: boolean;
  focus_style?: ComputedFocusStyle | null;
  focus_notes?: string | null;
}

export interface KeyboardIssue {
  issue_type: string;
  severity: 'critical' | 'serious' | 'moderate' | 'minor' | 'review_hint';
  step_index?: number | null;
  selector: string;
  message: string;
  recommendation: string;
  wcag_criteria: string[];
}

export interface KeyboardNavigationSummary {
  total_steps: number;
  forward_steps: number;
  reverse_steps: number;
  unique_elements: number;
  issues_count: number;
  has_potential_trap: boolean;
  missing_indicator_count: number;
  missing_name_count: number;
  positive_tabindex_count: number;
  completion_status: string;
}

export interface KeyboardNavigationReport {
  scan_id: string;
  page_id: string;
  page_url: string;
  viewport: { width: number; height: number };
  summary: KeyboardNavigationSummary;
  steps: KeyboardStep[];
  reverse_steps: KeyboardStep[];
  issues: KeyboardIssue[];
  disclaimer: string;
  tested_at: string;
}

export async function getKeyboardTestApi(
  scanId: string,
  pageId: string,
  forceRefresh = false
): Promise<KeyboardNavigationReport> {
  const response = await apiClient.get<KeyboardNavigationReport>(
    `/scans/${scanId}/pages/${pageId}/keyboard-test`,
    {
      params: { force_refresh: forceRefresh },
    }
  );
  return response.data;
}

export async function rerunKeyboardTestApi(
  scanId: string,
  pageId: string
): Promise<KeyboardNavigationReport> {
  const response = await apiClient.post<KeyboardNavigationReport>(
    `/scans/${scanId}/pages/${pageId}/keyboard-test/run`
  );
  return response.data;
}
