import { apiClient } from "./client";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type GeometryStatus =
  | "located"
  | "missing_target"
  | "hidden_or_zero_size"
  | "ambiguous"
  | "unsupported";

export interface HeatmapMarker {
  finding_id: string;
  rule_id: string;
  impact: string;
  description: string;
  help_url: string;
  selector: string | null;
  html: string | null;
  bounding_box: BoundingBox | null;
  geometry_status: GeometryStatus;
}

export interface HeatmapDensityPoint {
  x: number;
  y: number;
  weight: number;
  radius: number;
}

export interface HeatmapViewport {
  width: number;
  height: number;
  device_pixel_ratio: number;
}

export interface HeatmapResponse {
  page_id: string;
  url: string;
  screenshot_url: string | null;
  viewport: HeatmapViewport;
  markers: HeatmapMarker[];
  density_points: HeatmapDensityPoint[];
  total_violations: number;
  located_count: number;
  unlocated_count: number;
}

export interface ScanPageSummary {
  id: string;
  scan_id: string;
  url: string;
  status: string;
  title: string | null;
  violations_count: number;
  has_screenshot: boolean;
  viewport_width: number | null;
  viewport_height: number | null;
}

export async function listScanPagesApi(
  scanId: string
): Promise<ScanPageSummary[]> {
  const response = await apiClient.get<ScanPageSummary[]>(
    `/scans/${scanId}/pages`
  );
  return response.data;
}

export async function getPageHeatmapApi(
  scanId: string,
  pageId: string
): Promise<HeatmapResponse> {
  const response = await apiClient.get<HeatmapResponse>(
    `/scans/${scanId}/pages/${pageId}/heatmap`
  );
  return response.data;
}
