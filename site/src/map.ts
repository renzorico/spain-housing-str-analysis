// Map of active Barcelona listings, one quarter at a time.
import type { Feature, FeatureCollection, Point } from "geojson";
import * as maplibregl from "maplibre-gl";
import type { ExpressionSpecification, GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// MapLibre runs a web worker. Importing it with ?url makes Vite emit the
// file and hand back its final URL, in dev and in the production build.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";

import { loadPoints, type Points } from "./data";
import { cssVar, el, formatInt, formatQuarter, onThemeChange, requireElement, segmented } from "./ui";

maplibregl.setWorkerUrl(workerUrl);

// Free vector basemaps, no API key (https://openfreemap.org).
const STYLE_LIGHT = "https://tiles.openfreemap.org/styles/positron";
const STYLE_DARK = "https://tiles.openfreemap.org/styles/dark";
const BARCELONA: [number, number] = [2.165, 41.395];
const SOURCE_ID = "listings";
const LAYER_ID = "listings-dots";

type ColourMode = "band" | "licence" | "host";

interface Category {
  label: string;
  colourVar: string;
}

// Legend order and colours per mode, keyed by the code in the export.
const CATEGORIES: Record<ColourMode, Record<string, Category>> = {
  band: {
    tourist: { label: "Tourist (< 31 nights)", colourVar: "--tourist" },
    boundary: { label: "Boundary (31 nights)", colourVar: "--boundary" },
    seasonal: { label: "Seasonal (> 31 nights)", colourVar: "--seasonal" },
  },
  licence: {
    tourist_flat: { label: "Tourist licence", colourVar: "--tourist" },
    exempt_seasonal: { label: "Declared seasonal", colourVar: "--seasonal" },
    hotel_or_hostel: { label: "Hotel / hostel", colourVar: "--cat-4" },
    other_code: { label: "Other registration", colourVar: "--cat-5" },
    exempt_other: { label: "Other exemption", colourVar: "--cat-6" },
    missing: { label: "None shown", colourVar: "--cat-7" },
    other: { label: "Unreadable", colourVar: "--cat-7" },
  },
  host: {
    "1": { label: "1 listing", colourVar: "--cat-5" },
    "2-4": { label: "2–4 listings", colourVar: "--tourist" },
    "5-19": { label: "5–19 listings", colourVar: "--cat-4" },
    "20+": { label: "20+ listings", colourVar: "--seasonal" },
    unknown: { label: "Unknown", colourVar: "--cat-7" },
  },
};

// Which property of a feature holds each mode's code.
const PROPERTY: Record<ColourMode, "b" | "l" | "h"> = { band: "b", licence: "l", host: "h" };

const MODE_OPTIONS: { value: ColourMode; label: string }[] = [
  { value: "band", label: "Stay type" },
  { value: "licence", label: "Licence shown" },
  { value: "host", label: "Host size" },
];

function prefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function toGeoJson(points: Points): FeatureCollection<Point> {
  const features: Feature<Point>[] = points.lat.map((lat, i) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [points.lon[i] ?? 0, lat] },
    properties: {
      b: points.legend.band[points.band[i] ?? 0],
      l: points.legend.licence[points.licence[i] ?? 0],
      h: points.legend.host_size[points.host_size[i] ?? 0],
      r: points.legend.room[points.room[i] ?? 0],
      n: points.nights[i],
      p: points.price[i],
    },
  }));
  return { type: "FeatureCollection", features };
}

export async function initMap(snapshots: string[]): Promise<void> {
  const container = requireElement<HTMLDivElement>("map");
  const controls = requireElement<HTMLDivElement>("map-controls");
  const legend = requireElement<HTMLDivElement>("map-legend");

  let mode: ColourMode = "band";
  let snapshot = snapshots[snapshots.length - 1] ?? "";
  let data = toGeoJson(await loadPoints(snapshot));
  const hidden = new Set<string>();

  const map = new maplibregl.Map({
    container,
    style: prefersDark() ? STYLE_DARK : STYLE_LIGHT,
    center: BARCELONA,
    zoom: 12,
    minZoom: 10,
    maxZoom: 17,
    cooperativeGestures: true, // one finger scrolls the page on phones
    attributionControl: { compact: true, customAttribution: "Listings: Inside Airbnb (CC BY 4.0)" },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

  function colourExpression(): ExpressionSpecification {
    const pairs = Object.entries(CATEGORIES[mode]).flatMap(([code, category]) => [code, cssVar(category.colourVar)]);
    // MapLibre's type for "match" cannot express a variable number of
    // code/colour pairs, so the (valid) expression is cast through unknown.
    return ["match", ["get", PROPERTY[mode]], ...pairs, cssVar("--cat-7")] as unknown as ExpressionSpecification;
  }

  function filterExpression(): ExpressionSpecification | null {
    if (hidden.size === 0) return null;
    return ["!", ["in", ["get", PROPERTY[mode]], ["literal", [...hidden]]]];
  }

  function addLayer(): void {
    if (map.getSource(SOURCE_ID)) return;
    map.addSource(SOURCE_ID, { type: "geojson", data });
    map.addLayer({
      id: LAYER_ID,
      type: "circle",
      source: SOURCE_ID,
      paint: {
        "circle-color": colourExpression(),
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 1.2, 13, 2.6, 16, 6],
        "circle-opacity": 0.8,
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 13, 0, 16, 0.6],
        "circle-stroke-color": cssVar("--surface"),
      },
    });
    map.setFilter(LAYER_ID, filterExpression());
  }

  function restyle(): void {
    if (!map.getLayer(LAYER_ID)) return;
    map.setPaintProperty(LAYER_ID, "circle-color", colourExpression());
    map.setPaintProperty(LAYER_ID, "circle-stroke-color", cssVar("--surface"));
    map.setFilter(LAYER_ID, filterExpression());
    renderLegend();
  }

  // Airbnb added the "Exempt - seasonal rental" option to its licence form
  // between the Mar and Jun 2026 snapshots (see data/README.md).
  const SEASONAL_OPTION_FROM = "2026-06-01";

  function renderLegend(): void {
    const counts = new Map<string, number>();
    for (const feature of data.features) {
      const code = String(feature.properties?.[PROPERTY[mode]]);
      counts.set(code, (counts.get(code) ?? 0) + 1);
    }
    legend.replaceChildren(
      el("span", { class: "control-label" }, `${formatQuarter(snapshot)} · ${formatInt(data.features.length)} active listings`),
    );
    for (const [code, category] of Object.entries(CATEGORIES[mode])) {
      const count = counts.get(code) ?? 0;
      if (count === 0) continue;
      const item = el("button", {
        type: "button",
        class: "legend-item",
        "aria-pressed": String(!hidden.has(code)),
        title: "Show or hide this group",
      });
      const swatch = el("i");
      swatch.style.background = cssVar(category.colourVar);
      item.append(swatch, document.createTextNode(`${category.label} ${formatInt(count)}`));
      item.addEventListener("click", () => {
        if (hidden.has(code)) hidden.delete(code);
        else hidden.add(code);
        restyle();
      });
      legend.append(item);
    }
    if (mode === "licence" && snapshot < SEASONAL_OPTION_FROM) {
      legend.append(
        el("p", { class: "note" }, "Airbnb's form had no “declared seasonal” option before June 2026, so these listings show as “none shown”."),
      );
    }
  }

  map.on("style.load", () => {
    addLayer();
    renderLegend();
  });

  map.on("click", LAYER_ID, (event) => {
    const feature = event.features?.[0];
    if (!feature || feature.geometry.type !== "Point") return;
    const p = feature.properties as Record<string, string | number | null>;
    const licence = CATEGORIES.licence[String(p.l)]?.label ?? "—";
    const host = CATEGORIES.host[String(p.h)]?.label.toLowerCase() ?? "unknown";
    const price = p.p === null || p.p === undefined ? "no price shown" : `€${p.p} / night (asking)`;
    const body = el("div");
    body.append(
      el("strong", {}, String(p.r)),
      el("div", {}, `Minimum stay: ${p.n} night${p.n === 1 ? "" : "s"}`),
      el("div", {}, price),
      el("div", {}, `Licence shown: ${licence}`),
      el("div", {}, `Host runs ${host}`),
    );
    new maplibregl.Popup({ closeButton: true, maxWidth: "240px" })
      .setLngLat(feature.geometry.coordinates as [number, number])
      .setDOMContent(body)
      .addTo(map);
  });
  map.on("mouseenter", LAYER_ID, () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", LAYER_ID, () => (map.getCanvas().style.cursor = ""));

  controls.append(
    segmented("Colour by", MODE_OPTIONS, mode, (value) => {
      mode = value;
      hidden.clear();
      restyle();
    }),
    segmented(
      "Quarter",
      snapshots.map((s) => ({ value: s, label: formatQuarter(s) })),
      snapshot,
      async (value) => {
        snapshot = value;
        data = toGeoJson(await loadPoints(value));
        (map.getSource(SOURCE_ID) as GeoJSONSource | undefined)?.setData(data);
        renderLegend();
      },
    ),
  );

  onThemeChange(() => {
    // setStyle drops custom layers; style.load re-adds them with new colours.
    map.setStyle(prefersDark() ? STYLE_DARK : STYLE_LIGHT);
  });
}
