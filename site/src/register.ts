// The official HUT register against Airbnb listings.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import type { NeighbourhoodRow, Register } from "./data";
import { cssVar, el, formatInt, formatPct, formatQuarter, requireElement } from "./ui";

const LEGEND_WIDTH = 260;
const LEGEND_MARGIN = 14;

/** "2026_3T" -> "Q3 2026" */
function quarterLabel(code: string): string {
  const [year, quarter] = code.split("_");
  return `Q${(quarter ?? "").replace("T", "")} ${year ?? ""}`;
}

export function initRegister(register: Register, places: NeighbourhoodRow[]): void {
  const latest = register.match.at(-1);
  const total = register.totals[register.register_quarter];
  if (!latest || total === undefined) return;

  const tiles: [string, string][] = [
    [formatInt(total), `licensed tourist flats in Barcelona's register (${quarterLabel(register.register_quarter)})`],
    [formatPct(latest.match_register_pct, 0), `of licence numbers shown on Airbnb exist in the register (${formatQuarter(latest.snapshot)})`],
    [formatPct(latest.register_visible_pct, 0), "of registered flats appear on Airbnb with their number"],
  ];
  requireElement("register-stats").replaceChildren(
    ...tiles.map(([value, label]) => {
      const tile = el("div", { class: "stat" });
      tile.append(el("strong", {}, value), el("span", {}, label));
      return tile;
    }),
  );

  const data = places.filter((p) => p.active_listings > 0 || p.registered_huts > 0);
  const top = Math.max(...data.map((p) => Math.max(p.active_listings, p.registered_huts)));

  mountChart(requireElement("register-chart"), (width) => {
    const plot = Plot.plot({
      width,
      height: Math.min(width, 440),
      marginLeft: 48,
      style: plotStyle(),
      x: { label: "registered tourist flats (official) →", domain: [0, top], grid: true },
      y: { label: "↑ active Airbnb listings", domain: [0, top], grid: true },
      color: {
        type: "linear",
        domain: [0, 80],
        range: [cssVar("--tourist"), cssVar("--seasonal")],
        label: "% asking 31+ nights",
      },
      marks: [
        Plot.line([[0, 0], [top, top]], { stroke: cssVar("--muted"), strokeDasharray: "3,3" }),
        Plot.dot(data, {
          x: "registered_huts",
          y: "active_listings",
          fill: (p: NeighbourhoodRow) => p.share_month_plus ?? 0,
          r: 5,
          fillOpacity: 0.85,
          stroke: cssVar("--surface"),
          tip: true,
          title: (p: NeighbourhoodRow) =>
            [
              `${p.neighbourhood} (${p.district})`,
              `${formatInt(p.registered_huts)} registered flats`,
              `${formatInt(p.active_listings)} active listings, ${formatInt(p.with_tourist_licence)} showing a licence`,
              p.share_month_plus === null ? "" : `${formatPct(p.share_month_plus, 0)} ask 31+ nights`,
            ]
              .filter(Boolean)
              .join("\n"),
        }),
      ],
    });
    plot.setAttribute("aria-label", "Scatter plot: registered tourist flats against active Airbnb listings, one dot per Barcelona neighbourhood.");
    // Legend drawn separately: the built-in one has no side margins, so its
    // end labels overhang at phone width.
    const legend = plot.legend("color", { marginLeft: LEGEND_MARGIN, marginRight: LEGEND_MARGIN, width: LEGEND_WIDTH, style: plotStyle() });
    const wrapper = el("div");
    if (legend) wrapper.append(legend);
    wrapper.append(plot);
    return wrapper;
  });
}
