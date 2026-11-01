import { useState, useMemo, useRef, useEffect } from "react";
import {
  AlertTriangle,
  Eye,
  Layers,
  MapPin,
  Table as TableIcon,
  ExternalLink,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import {
  HeatmapResponse,
  ScanPageSummary,
} from "../../api/heatmap";

export interface VisualHeatmapViewerProps {
  heatmapData: HeatmapResponse | null;
  pages: ScanPageSummary[];
  selectedPageId: string;
  onSelectPage: (pageId: string) => void;
  isLoading?: boolean;
  onInspectFinding?: (findingId: string) => void;
}

export function VisualHeatmapViewer({
  heatmapData,
  pages,
  selectedPageId,
  onSelectPage,
  isLoading = false,
  onInspectFinding,
}: VisualHeatmapViewerProps) {
  const [viewMode, setViewMode] = useState<"visual" | "table">("visual");
  const [showDensity, setShowDensity] = useState<boolean>(true);
  const [showMarkers, setShowMarkers] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [selectedMarkerId, setSelectedMarkerId] = useState<string | null>(null);
  const [hoveredMarkerId, setHoveredMarkerId] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Filter markers based on severity
  const markers = heatmapData?.markers;
  const filteredMarkers = useMemo(() => {
    if (!markers) return [];
    if (severityFilter === "all") return markers;
    return markers.filter((m) => m.impact.toLowerCase() === severityFilter);
  }, [markers, severityFilter]);

  const locatedMarkers = useMemo(
    () => filteredMarkers.filter((m) => m.geometry_status === "located" && m.bounding_box),
    [filteredMarkers]
  );

  const unlocatedMarkers = useMemo(
    () => filteredMarkers.filter((m) => m.geometry_status !== "located" || !m.bounding_box),
    [filteredMarkers]
  );

  // Selected marker object
  const activeMarker = useMemo(
    () => heatmapData?.markers.find((m) => m.finding_id === selectedMarkerId) || null,
    [heatmapData?.markers, selectedMarkerId]
  );

  // Viewport dimensions
  const viewportWidth = heatmapData?.viewport?.width || 1280;
  const viewportHeight = heatmapData?.viewport?.height || 800;

  // Draw thermal density overlay on HTML5 Canvas
  useEffect(() => {
    if (!canvasRef.current || !showDensity || viewMode !== "visual" || !heatmapData) return;

    const canvas = canvasRef.current;
    canvas.width = viewportWidth;
    canvas.height = viewportHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const points = heatmapData.density_points || [];
    if (points.length === 0) return;

    points.forEach((pt) => {
      const grad = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, pt.radius);
      const alpha = Math.min(0.65, pt.weight * 0.45);
      grad.addColorStop(0, `rgba(244, 63, 94, ${alpha})`);
      grad.addColorStop(0.4, `rgba(249, 115, 22, ${alpha * 0.7})`);
      grad.addColorStop(0.7, `rgba(251, 191, 36, ${alpha * 0.4})`);
      grad.addColorStop(1, "rgba(56, 189, 248, 0)");

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, pt.radius, 0, 2 * Math.PI);
      ctx.fill();
    });
  }, [showDensity, viewMode, heatmapData, viewportWidth, viewportHeight]);

  const getImpactColor = (impact: string) => {
    switch (impact.toLowerCase()) {
      case "critical":
        return "#FB7185";
      case "serious":
        return "#F97316";
      case "moderate":
        return "#FBBF24";
      case "minor":
        return "#38BDF8";
      default:
        return "#9CA3AF";
    }
  };

  const getImpactBadgeVariant = (impact: string) => {
    switch (impact.toLowerCase()) {
      case "critical":
        return "critical";
      case "serious":
        return "serious";
      case "moderate":
        return "moderate";
      case "minor":
        return "minor";
      default:
        return "primary";
    }
  };

  return (
    <div className="space-y-4">
      {/* Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-[#303741] bg-[#171C23]">
        <div className="flex flex-wrap items-center gap-3">
          {/* Page Selector */}
          {pages.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="heatmap-page-select" className="text-xs font-medium text-[#9CA3AF]">
                Audited Page:
              </label>
              <select
                id="heatmap-page-select"
                value={selectedPageId}
                onChange={(e) => onSelectPage(e.target.value)}
                className="h-8 rounded-lg border border-[#303741] bg-[#1D2229] px-2.5 py-1 text-xs text-[#F3F4F6] focus:border-[#38BDF8] focus:outline-none"
              >
                {pages.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.url} ({p.violations_count} issues)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5 border-l border-[#303741] pl-3">
            <span className="text-xs text-[#9CA3AF]">Severity:</span>
            {(["all", "critical", "serious", "moderate", "minor"] as const).map((sev) => (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium capitalize transition-colors ${
                  severityFilter === sev
                    ? "bg-[#38BDF8] text-[#090D11]"
                    : "text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-[#252C35]"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* View / Overlay Toggles */}
        <div className="flex items-center gap-2">
          {viewMode === "visual" && (
            <>
              <Button
                type="button"
                variant={showDensity ? "default" : "outline"}
                size="sm"
                onClick={() => setShowDensity(!showDensity)}
                className="text-xs gap-1.5 h-8 px-2.5"
                title="Toggle Thermal Density Overlay"
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Density</span>
              </Button>

              <Button
                type="button"
                variant={showMarkers ? "default" : "outline"}
                size="sm"
                onClick={() => setShowMarkers(!showMarkers)}
                className="text-xs gap-1.5 h-8 px-2.5"
                title="Toggle Element Bounding Boxes"
              >
                <MapPin className="h-3.5 w-3.5" />
                <span>Markers</span>
              </Button>
            </>
          )}

          <div className="flex rounded-lg border border-[#303741] bg-[#111315] p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("visual")}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === "visual"
                  ? "bg-[#252C35] text-[#38BDF8]"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
              title="Interactive Visual Overlay"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>Canvas</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === "table"
                  ? "bg-[#252C35] text-[#38BDF8]"
                  : "text-[#9CA3AF] hover:text-[#F3F4F6]"
              }`}
              title="Accessible Table Fallback"
            >
              <TableIcon className="h-3.5 w-3.5" />
              <span>Accessible Table</span>
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-96 items-center justify-center rounded-xl border border-[#303741] bg-[#171C23]">
          <div className="flex flex-col items-center gap-3">
            <div className="h-7 w-7 animate-spin rounded-full border-2 border-[#38BDF8] border-t-transparent" />
            <p className="text-xs text-[#9CA3AF]">Loading visual accessibility heatmap telemetry...</p>
          </div>
        </div>
      ) : !heatmapData ? (
        <div className="flex h-64 items-center justify-center rounded-xl border border-[#303741] bg-[#171C23] p-6 text-center">
          <div>
            <AlertTriangle className="mx-auto h-8 w-8 text-[#FB7185] mb-2" />
            <h3 className="text-sm font-semibold text-[#F3F4F6]">Heatmap Data Unavailable</h3>
            <p className="text-xs text-[#9CA3AF] mt-1 max-w-md">
              No page audits or visual telemetry were found for this scan. Ensure the target page completed audit.
            </p>
          </div>
        </div>
      ) : viewMode === "visual" ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Main Screenshot & Overlay Area */}
          <div className="lg:col-span-3 space-y-3">
            <div className="relative rounded-xl border border-[#303741] bg-[#111315] overflow-auto max-h-[700px] shadow-inner">
              {heatmapData.screenshot_url ? (
                <div
                  className="relative mx-auto"
                  style={{
                    width: `${viewportWidth}px`,
                    height: `${viewportHeight}px`,
                  }}
                >
                  {/* Base Screenshot */}
                  <img
                    src={heatmapData.screenshot_url}
                    alt={`Audit screenshot for ${heatmapData.url}`}
                    className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
                  />

                  {/* HTML5 Canvas Density Overlay */}
                  {showDensity && (
                    <canvas
                      ref={canvasRef}
                      className="absolute inset-0 w-full h-full pointer-events-none mix-blend-screen opacity-85"
                    />
                  )}

                  {/* SVG / Interactive Bounding Boxes */}
                  {showMarkers && (
                    <div className="absolute inset-0 w-full h-full">
                      {locatedMarkers.map((marker, index) => {
                        const box = marker.bounding_box;
                        if (!box) return null;

                        const isSelected = selectedMarkerId === marker.finding_id;
                        const isHovered = hoveredMarkerId === marker.finding_id;
                        const strokeColor = getImpactColor(marker.impact);

                        return (
                          <div
                            key={marker.finding_id}
                            style={{
                              position: "absolute",
                              left: `${box.x}px`,
                              top: `${box.y}px`,
                              width: `${Math.max(box.width, 16)}px`,
                              height: `${Math.max(box.height, 16)}px`,
                              border: `2px solid ${strokeColor}`,
                              backgroundColor: isSelected
                                ? `${strokeColor}33`
                                : isHovered
                                ? `${strokeColor}22`
                                : `${strokeColor}11`,
                              zIndex: isSelected ? 40 : isHovered ? 30 : 10,
                              cursor: "pointer",
                              transition: "all 0.15s ease",
                              borderRadius: "4px",
                            }}
                            onClick={() => setSelectedMarkerId(marker.finding_id)}
                            onMouseEnter={() => setHoveredMarkerId(marker.finding_id)}
                            onMouseLeave={() => setHoveredMarkerId(null)}
                            title={`${marker.rule_id} (${marker.impact}): ${marker.description}`}
                          >
                            {/* Marker Number Badge */}
                            <span
                              style={{
                                position: "absolute",
                                top: "-10px",
                                left: "-10px",
                                backgroundColor: strokeColor,
                                color: "#090D11",
                                fontSize: "10px",
                                fontWeight: "bold",
                                width: "18px",
                                height: "18px",
                                borderRadius: "50%",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                boxShadow: "0 2px 4px rgba(0,0,0,0.5)",
                              }}
                            >
                              {index + 1}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-12 text-center">
                  <AlertTriangle className="h-10 w-10 text-[#FBBF24] mb-3" />
                  <h4 className="text-sm font-semibold text-[#F3F4F6]">Screenshot Not Captured</h4>
                  <p className="text-xs text-[#9CA3AF] max-w-md mt-1">
                    Visual telemetry coordinates are present, but screenshot artifact is not available.
                    You can inspect all finding coordinates in the Accessible Table view.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setViewMode("table")}
                    className="mt-4 text-xs gap-1.5"
                  >
                    <TableIcon className="h-3.5 w-3.5" />
                    Switch to Accessible Table
                  </Button>
                </div>
              )}
            </div>

            {/* Location Unavailable Indicators */}
            {unlocatedMarkers.length > 0 && (
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3.5 text-xs text-[#FBBF24]">
                <div className="flex items-center gap-2 font-medium">
                  <HelpCircle className="h-4 w-4 shrink-0" />
                  <span>
                    {unlocatedMarkers.length} findings could not be visually anchored ({unlocatedMarkers.map((m) => m.geometry_status).filter((v, i, a) => a.indexOf(v) === i).join(", ")}):
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {unlocatedMarkers.map((m) => (
                    <button
                      key={m.finding_id}
                      type="button"
                      onClick={() => setSelectedMarkerId(m.finding_id)}
                      className="px-2 py-0.5 rounded border border-[#303741] bg-[#171C23] text-[11px] font-mono text-[#F3F4F6] hover:border-[#38BDF8]"
                    >
                      {m.rule_id} ({m.geometry_status})
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar: Selected Finding Detail / Finding List */}
          <div className="space-y-3">
            {activeMarker ? (
              <div className="rounded-xl border border-[#303741] bg-[#171C23] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-[#9CA3AF] uppercase tracking-wider">
                    Finding Telemetry
                  </span>
                  <Badge variant={getImpactBadgeVariant(activeMarker.impact)} className="capitalize text-xs">
                    {activeMarker.impact}
                  </Badge>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-[#F3F4F6] font-mono">{activeMarker.rule_id}</h4>
                  <p className="text-xs text-[#D1D5DB] mt-1 line-clamp-3">{activeMarker.description}</p>
                </div>

                {activeMarker.selector && (
                  <div className="space-y-1">
                    <span className="text-[11px] text-[#9CA3AF]">Target Selector:</span>
                    <pre className="p-2 rounded bg-[#111315] border border-[#303741] text-[11px] font-mono text-[#38BDF8] break-all whitespace-pre-wrap max-h-24 overflow-y-auto">
                      {activeMarker.selector}
                    </pre>
                  </div>
                )}

                {activeMarker.bounding_box && (
                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-[#111315] p-2.5 rounded-lg border border-[#303741]">
                    <div>
                      <span className="text-[#9CA3AF]">X, Y: </span>
                      <span className="text-[#F3F4F6]">
                        {Math.round(activeMarker.bounding_box.x)}, {Math.round(activeMarker.bounding_box.y)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#9CA3AF]">Size: </span>
                      <span className="text-[#F3F4F6]">
                        {Math.round(activeMarker.bounding_box.width)} × {Math.round(activeMarker.bounding_box.height)}
                      </span>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2 pt-2 border-t border-[#303741]">
                  {activeMarker.help_url && (
                    <a
                      href={activeMarker.help_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-[#38BDF8] hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>axe Documentation</span>
                    </a>
                  )}

                  {onInspectFinding && (
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => onInspectFinding(activeMarker.finding_id)}
                      className="ml-auto text-xs gap-1.5 h-7 px-2.5"
                    >
                      <Sparkles className="h-3 w-3" />
                      <span>Inspect</span>
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-[#303741] bg-[#171C23] p-4 text-center">
                <MapPin className="mx-auto h-6 w-6 text-[#9CA3AF] mb-2" />
                <h5 className="text-xs font-semibold text-[#F3F4F6]">Click a Marker to Inspect</h5>
                <p className="text-[11px] text-[#9CA3AF] mt-1">
                  Select any highlighted violation boundary on the canvas to inspect its DOM coordinates and rule definition.
                </p>
              </div>
            )}

            {/* List of Located Findings */}
            <div className="rounded-xl border border-[#303741] bg-[#171C23] p-3 max-h-96 overflow-y-auto space-y-2">
              <span className="text-[11px] font-semibold text-[#9CA3AF] uppercase tracking-wider block mb-2">
                All Violations ({filteredMarkers.length})
              </span>
              {filteredMarkers.map((m, idx) => (
                <div
                  key={m.finding_id}
                  onClick={() => setSelectedMarkerId(m.finding_id)}
                  onMouseEnter={() => setHoveredMarkerId(m.finding_id)}
                  onMouseLeave={() => setHoveredMarkerId(null)}
                  className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                    selectedMarkerId === m.finding_id
                      ? "border-[#38BDF8] bg-[#252C35]"
                      : hoveredMarkerId === m.finding_id
                      ? "border-[#38BDF8]/50 bg-[#1D2229]"
                      : "border-[#303741] bg-[#111315] hover:border-[#38BDF8]/40"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono font-semibold text-[#F3F4F6] truncate">
                      {idx + 1}. {m.rule_id}
                    </span>
                    <Badge variant={getImpactBadgeVariant(m.impact)} className="text-[10px] uppercase">
                      {m.impact}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-[#9CA3AF] mt-1 truncate">{m.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Accessible Table Fallback */
        <div className="rounded-xl border border-[#303741] bg-[#171C23] overflow-hidden">
          <div className="p-3 border-b border-[#303741] bg-[#111315] flex items-center justify-between">
            <h3 className="text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider">
              Accessible Heatmap Telemetry Table
            </h3>
            <span className="text-xs text-[#9CA3AF]">
              Showing {filteredMarkers.length} findings ({locatedMarkers.length} with coordinates)
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" aria-label="Accessibility findings and coordinate coordinates">
              <thead className="bg-[#1D2229] text-[11px] font-semibold text-[#9CA3AF] uppercase tracking-wider border-b border-[#303741]">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Rule ID</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Selector</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Coordinates (X, Y, W, H)</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#303741]">
                {filteredMarkers.map((m, index) => {
                  const box = m.bounding_box;
                  return (
                    <tr key={m.finding_id} className="hover:bg-[#252C35]/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-[#9CA3AF]">{index + 1}</td>
                      <td className="px-4 py-3 font-mono font-bold text-[#F3F4F6]">{m.rule_id}</td>
                      <td className="px-4 py-3">
                        <Badge variant={getImpactBadgeVariant(m.impact)} className="capitalize text-[10px]">
                          {m.impact}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-[#38BDF8] max-w-xs truncate">
                        {m.selector || "N/A"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono ${
                            m.geometry_status === "located"
                              ? "bg-emerald-500/10 text-[#34D399]"
                              : "bg-amber-500/10 text-[#FBBF24]"
                          }`}
                        >
                          {m.geometry_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-[#9CA3AF]">
                        {box ? (
                          `${Math.round(box.x)}, ${Math.round(box.y)}, ${Math.round(box.width)}, ${Math.round(
                            box.height
                          )}`
                        ) : (
                          <span className="text-[#6B7280]">Unavailable</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {onInspectFinding && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => onInspectFinding(m.finding_id)}
                            className="text-xs h-7 px-2"
                          >
                            Inspect
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
