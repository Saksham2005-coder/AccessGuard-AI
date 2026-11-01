import { apiClient } from "./client";

export interface SemanticNode {
  sequence_index: number;
  role: string;
  accessible_name: string | null;
  description: string | null;
  heading_level: number | null;
  landmark_type: string | null;
  is_interactive: boolean;
  selector: string;
  tag_name: string;
  has_name: boolean;
  attributes: Record<string, unknown>;
  associated_finding_id: string | null;
  potential_issue: string | null;
}

export interface HeadingOutlineItem {
  level: number;
  text: string;
  sequence_index: number;
  selector: string;
  is_skipped: boolean;
}

export interface LandmarkOutlineItem {
  landmark_type: string;
  accessible_name: string | null;
  sequence_index: number;
  selector: string;
}

export interface ReviewHint {
  category: "missing_name" | "heading_skip" | "duplicate_name" | "generic_role";
  message: string;
  severity: "warning" | "advisory";
  sequence_index: number;
  selector: string;
  associated_finding_id: string | null;
}

export interface ScreenReaderSimulationResponse {
  scan_id: string;
  page_id: string;
  page_url: string;
  nodes_count: number;
  reading_order: SemanticNode[];
  headings: HeadingOutlineItem[];
  landmarks: LandmarkOutlineItem[];
  interactive_elements: SemanticNode[];
  review_hints: ReviewHint[];
  disclaimer: string;
  limitations: string[];
  captured_at: string;
}

export async function getScreenReaderSimulationApi(
  scanId: string,
  pageId: string,
  forceRefresh = false
): Promise<ScreenReaderSimulationResponse> {
  const response = await apiClient.get<ScreenReaderSimulationResponse>(
    `/scans/${scanId}/pages/${pageId}/screen-reader-simulation`,
    { params: { force_refresh: forceRefresh } }
  );
  return response.data;
}
