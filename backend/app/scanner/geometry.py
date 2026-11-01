"""Element bounding box geometry capture and density computation for visual heatmaps."""

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """2D rectangular coordinates in document pixels."""

    x: float = Field(..., description="Horizontal offset in pixels from left edge")
    y: float = Field(..., description="Vertical offset in pixels from top edge")
    width: float = Field(..., description="Width of bounding rectangle in pixels")
    height: float = Field(..., description="Height of bounding rectangle in pixels")


class ElementGeometryResult(BaseModel):
    """DOM location status and bounding box for a given selector."""

    selector: str
    status: str = Field(
        ...,
        description="Geometry status: located, not_located, ambiguous, or stale",
    )
    bounding_box: BoundingBox | None = None
    match_count: int = 0


class HeatmapDensityPoint(BaseModel):
    """Thermal density point representation for canvas and SVG overlay rendering."""

    x: float
    y: float
    intensity: float
    radius: float
    impact: str
    finding_id: str | None = None


IMPACT_WEIGHTS: dict[str, float] = {
    "critical": 1.0,
    "serious": 0.75,
    "moderate": 0.5,
    "minor": 0.25,
}

IMPACT_RADII: dict[str, float] = {
    "critical": 65.0,
    "serious": 50.0,
    "moderate": 40.0,
    "minor": 30.0,
}


async def capture_element_geometries(
    page: Any,
    selectors: Sequence[str],
) -> dict[str, ElementGeometryResult]:
    """Capture bounding box coordinates directly from live Playwright page DOM.

    Safely evaluates selector bounds, accounting for page scroll offsets and ambiguity.
    """
    if not selectors:
        return {}

    # Pass selectors as parameterized data to prevent arbitrary script injection
    unique_selectors = list(dict.fromkeys(selectors))

    raw_results = await page.evaluate(
        """(sels) => {
            const scrollX = window.scrollX || window.pageXOffset || 0;
            const scrollY = window.scrollY || window.pageYOffset || 0;

            return sels.map(sel => {
                if (!sel || typeof sel !== 'string') {
                    return { selector: sel, status: 'not_located', box: null, count: 0 };
                }
                try {
                    const matches = document.querySelectorAll(sel);
                    const count = matches.length;

                    if (count === 0) {
                        return { selector: sel, status: 'not_located', box: null, count: 0 };
                    }

                    const el = matches[0];
                    const rect = el.getBoundingClientRect();

                    // Elements with zero dimensions or display:none
                    if (rect.width <= 0 && rect.height <= 0) {
                        return { selector: sel, status: 'not_located', box: null, count: count };
                    }

                    const box = {
                        x: Math.round(rect.left + scrollX),
                        y: Math.round(rect.top + scrollY),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };

                    const status = count > 1 ? 'ambiguous' : 'located';
                    return { selector: sel, status: status, box: box, count: count };
                } catch (e) {
                    return { selector: sel, status: 'not_located', box: null, count: 0 };
                }
            });
        }""",
        unique_selectors,
    )

    results: dict[str, ElementGeometryResult] = {}
    for item in raw_results:
        sel = item["selector"]
        box_data = item.get("box")
        bbox = BoundingBox(**box_data) if box_data else None
        results[sel] = ElementGeometryResult(
            selector=sel,
            status=item.get("status", "not_located"),
            bounding_box=bbox,
            match_count=item.get("count", 0),
        )

    return results


def calculate_density_hotspots(
    markers: Sequence[dict[str, Any]],
) -> list[HeatmapDensityPoint]:
    """Calculate thermal density points from positioned findings and impact weights."""
    density_points: list[HeatmapDensityPoint] = []

    for m in markers:
        bbox = m.get("bounding_box")
        if not bbox:
            continue

        x = float(bbox.get("x", 0))
        y = float(bbox.get("y", 0))
        width = float(bbox.get("width", 0))
        height = float(bbox.get("height", 0))

        # Center point of the element
        center_x = round(x + (width / 2.0), 1)
        center_y = round(y + (height / 2.0), 1)

        impact = str(m.get("impact", "moderate")).lower()
        weight = IMPACT_WEIGHTS.get(impact, 0.5)
        radius = IMPACT_RADII.get(impact, 40.0)

        density_points.append(
            HeatmapDensityPoint(
                x=center_x,
                y=center_y,
                intensity=weight,
                radius=radius,
                impact=impact,
                finding_id=m.get("finding_id"),
            )
        )

    return density_points
