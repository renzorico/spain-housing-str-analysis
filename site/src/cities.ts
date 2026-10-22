// Five cities, December vs September: one measure at a time.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import { CITIES, CITY_LABELS, type CityRow, type SnapshotSummary } from "./data";
import { cssVar, formatDay, POPULATION, requireElement, segmented } from "./ui";

const FIRST_ROUND = "Dec 2025";
const LAST_ROUND = "Sep 2026";

type Measure = keyof Pick<
  SnapshotSummary,
  "share_month_plus" | "share_31_nights" | "share_tourist_licence" | "share_professional" | "share_entire_home" | "median_price"
>;

interface MeasureInfo {
  label: string;
  axis: string;
  note: string;
}

const MEASURES: Record<Measure, MeasureInfo> = {
  share_month_plus: {
    label: "31+ nights",
    axis: `% of ${POPULATION} asking 31+ nights →`,
    note: "31+ nights is a common measurement threshold, not a legal rule shared by every region: the legal lines differ between regions.",
  },
  share_31_nights: {
    label: "Exactly 31",
    axis: `% of ${POPULATION} asking exactly 31 nights →`,
    note: "31 nights sits on the Catalan legal line. Outside Catalonia it has no special legal meaning.",
  },
  share_tourist_licence: {
    label: "Tourist licence",
    axis: `% of ${POPULATION} showing a tourist-flat licence →`,
    note: "Outside Catalonia this is a lower bound: only confirmed regional codes are counted. Airbnb's licence form also changed in June 2026, in every city.",
  },
  share_professional: {
    label: "Accounts with 5+",
    axis: `% of ${POPULATION} run by host accounts with 5+ listings →`,
    note: "A host account's listing count is per city, as reported by Inside Airbnb. An account is not necessarily one owner or one company.",
  },
  share_entire_home: {
    label: "Entire homes",
    axis: `% of ${POPULATION} that are entire homes →`,
    note: "The rest are private rooms, shared rooms and hotel rooms.",
  },
  median_price: {
    label: "Median price",
    axis: "median asking price per night (€) →",
    note: "Asking prices, not what guests paid. December 2025 snapshots have no prices, so only September is shown.",
  },
};

interface Row {
  city: string;
  round: string;
  value: number;
}

export function initCities(cities: CityRow[]): void {
  const controls = requireElement("cities-controls");
  const chart = requireElement("cities-chart");
  const note = requireElement("cities-note");

  // The five cities were not scraped on the same days: say which days.
  const scrapeDates = CITIES.map((city) => {
    const dates = cities.find((c) => c.city === city)?.scrape_dates ?? {};
    return `${CITY_LABELS[city]} ${formatDay(dates[FIRST_ROUND] ?? "")} / ${formatDay(dates[LAST_ROUND] ?? "")}`;
  }).join("; ");

  let measure: Measure = "share_month_plus";
  let render = () => {};

  function rows(): Row[] {
    return CITIES.flatMap((city) => {
      const row = cities.find((c) => c.city === city);
      return [FIRST_ROUND, LAST_ROUND].flatMap((round) => {
        const value = row?.rounds[round]?.[measure];
        return typeof value === "number" ? [{ city: CITY_LABELS[city], round, value }] : [];
      });
    });
  }

  function draw(width: number): Element {
    const data = rows();
    const isPrice = measure === "median_price";
    const firstColour = cssVar("--boundary");
    const lastColour = cssVar("--accent");
    const plot = Plot.plot({
      width,
      height: 240,
      marginLeft: 80,
      style: plotStyle(),
      x: { label: MEASURES[measure].axis, grid: true, nice: true, zero: !isPrice },
      y: { label: null, domain: CITIES.map((c) => CITY_LABELS[c]) },
      color: { domain: [FIRST_ROUND, LAST_ROUND], range: [firstColour, lastColour], legend: true },
      marks: [
        // A line from December to September for each city ("dumbbell").
        Plot.link(
          CITIES.map((c) => CITY_LABELS[c]),
          {
            y1: (city: string) => city,
            y2: (city: string) => city,
            x1: (city: string) => data.find((d) => d.city === city && d.round === FIRST_ROUND)?.value ?? null,
            x2: (city: string) => data.find((d) => d.city === city && d.round === LAST_ROUND)?.value ?? null,
            stroke: cssVar("--line"),
            strokeWidth: 3,
          },
        ),
        Plot.dot(data, {
          x: "value",
          y: "city",
          fill: "round",
          r: 6,
          tip: true,
          title: (d: Row) => `${d.city}, ${d.round}: ${isPrice ? `€${Math.round(d.value)}` : `${d.value}%`}`,
        }),
      ],
    });
    plot.setAttribute("aria-label", `Dot chart: ${MEASURES[measure].axis.replace(" →", "")}, by city, ${FIRST_ROUND} and ${LAST_ROUND}.`);
    note.textContent = `${MEASURES[measure].note} Scrape dates: ${scrapeDates}.`;
    return plot;
  }

  controls.append(
    segmented(
      "Measure",
      (Object.keys(MEASURES) as Measure[]).map((m) => ({ value: m, label: MEASURES[m].label })),
      measure,
      (value) => {
        measure = value;
        render();
      },
    ),
  );
  render = mountChart(chart, draw);
}
