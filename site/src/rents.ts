// Average rent of new leases in Barcelona, with the policy dates.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import type { Meta, RentRow } from "./data";
import { cssVar, formatCalendarQuarter, formatInt, requireElement, segmented } from "./ui";

type View = "level" | "yoy";

// Policy dates drawn on the chart, read from config via meta.json.
// Full and short labels: two markers two years apart collide at phone width.
const NARROW_WIDTH = 520;
const MARKED_LEVERS: Record<string, { full: string; short: string }> = {
  rent_cap: { full: "rent limit", short: "limit" },
  seasonal_rentals: { full: "limit on seasonal lets", short: "seasonal" },
};

interface Point {
  date: Date;
  value: number;
  row: RentRow;
}

export function initRents(rents: RentRow[], meta: Meta): void {
  let view: View = "level";
  let render = () => {};

  const markerDates = Object.entries(MARKED_LEVERS).flatMap(([id, labels]) => {
    const lever = meta.policy_levers[id];
    return lever ? [{ date: new Date(`${lever.applies_from}T00:00:00`), labels }] : [];
  });

  function points(): Point[] {
    return rents.flatMap((row) => {
      const value = view === "level" ? row.avg_rent : row.yoy_pct;
      return value === null ? [] : [{ date: new Date(`${row.quarter_start}T00:00:00`), value, row }];
    });
  }

  function draw(width: number): Element {
    const data = points();
    const isLevel = view === "level";
    const markers = markerDates.map((m) => ({ date: m.date, label: width < NARROW_WIDTH ? m.labels.short : m.labels.full }));
    const plot = Plot.plot({
      width,
      height: 300,
      marginLeft: 48,
      marginTop: 24,
      style: plotStyle(),
      x: { label: null, type: "utc" },
      y: { label: isLevel ? "↑ € per month" : "↑ change vs same quarter a year earlier (%)", grid: true, nice: true, zero: !isLevel },
      marks: [
        isLevel ? null : Plot.ruleY([0], { stroke: cssVar("--muted") }),
        Plot.ruleX(markers, { x: "date", stroke: cssVar("--text"), strokeDasharray: "4,3" }),
        // Labels sit left of their line: the latest date is near the right edge.
        Plot.text(markers, { x: "date", text: "label", frameAnchor: "top", dy: -14, dx: -4, textAnchor: "end", fill: cssVar("--muted") }),
        Plot.line(data, { x: "date", y: "value", stroke: cssVar("--accent"), strokeWidth: 2 }),
        Plot.dot(data, {
          x: "date",
          y: "value",
          r: 2.5,
          fill: cssVar("--accent"),
          tip: true,
          title: (p: Point) => {
            const quarter = formatCalendarQuarter(p.row.quarter_start);
            const change = p.row.yoy_pct === null ? "" : `\n${p.row.yoy_pct > 0 ? "+" : ""}${p.row.yoy_pct}% on a year earlier`;
            return `${quarter}: €${formatInt(Math.round(p.row.avg_rent))} / month${change}\n${formatInt(p.row.new_leases)} new leases`;
          },
        }),
      ],
    });
    plot.setAttribute("aria-label", "Line chart: average monthly rent of new leases in Barcelona, by quarter, with policy dates marked.");
    return plot;
  }

  requireElement("rents-controls").append(
    segmented(
      "Show",
      [
        { value: "level" as const, label: "Average rent" },
        { value: "yoy" as const, label: "Year-on-year change" },
      ],
      view,
      (value) => {
        view = value;
        render();
      },
    ),
  );
  render = mountChart(requireElement("rents-chart"), draw);
}
