// "Where did December's listings go?" and the exit-gap comparison.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import { BANDS, CITIES, CITY_LABELS, type Band, type City, type CityRow, type TransitionTable, type Transitions } from "./data";
import { cssVar, el, formatInt, formatPct, formatQuarter, POPULATION, requireElement, segmented } from "./ui";

const BAND_LABELS: Record<Band, string> = {
  tourist: "Tourist (<31)",
  boundary: "Boundary (31)",
  seasonal: "Seasonal (>31)",
};

const OUTCOMES = ["same band", "other band", "listed, no open dates", "absent from later scrape"] as const;
type Outcome = (typeof OUTCOMES)[number];
const OUTCOME_COLOURS: Record<Outcome, string> = {
  "same band": "--cat-5",
  "other band": "--cat-4",
  "listed, no open dates": "--boundary",
  "absent from later scrape": "--cat-6",
};

interface Segment {
  band: string;
  outcome: Outcome;
  listings: number;
  share: number;
}

function segments(table: TransitionTable): Segment[] {
  const column = (name: string) => table.to.indexOf(name);
  return table.from.flatMap((band, row) => {
    const counts = table.counts[row] ?? [];
    const at = (name: string) => counts[column(name)] ?? 0;
    const total = counts.reduce((sum, n) => sum + n, 0);
    const same = at(band);
    const otherBand = BANDS.filter((b) => b !== band).reduce((sum, b) => sum + at(b), 0);
    const values: Record<Outcome, number> = {
      "same band": same,
      "other band": otherBand,
      "listed, no open dates": at("inactive"),
      "absent from later scrape": at("gone"),
    };
    return OUTCOMES.map((outcome) => ({
      band: BAND_LABELS[band],
      outcome,
      listings: values[outcome],
      share: total ? (values[outcome] / total) * 100 : 0,
    }));
  });
}

export function initFlows(transitions: Transitions): void {
  const controls = requireElement("flows-controls");
  const chart = requireElement("flows-chart");

  let city: City = "barcelona";
  let periodIndex = -1; // -1 = first to last snapshot; otherwise a Barcelona quarter
  let render = () => {};

  const table = (): TransitionTable =>
    city === "barcelona" && periodIndex >= 0
      ? (transitions.barcelona_quarters[periodIndex] ?? transitions.cities.barcelona)
      : transitions.cities[city];

  const periodGroup = el("div");
  function renderPeriodControl(): void {
    if (city !== "barcelona") {
      periodGroup.replaceChildren();
      return;
    }
    const whole = transitions.cities.barcelona;
    const options = [
      { value: "-1", label: `${formatQuarter(whole.from_snapshot)} → ${formatQuarter(whole.to_snapshot)}` },
      ...transitions.barcelona_quarters.map((q, i) => ({
        value: String(i),
        label: `${formatQuarter(q.from_snapshot)} → ${formatQuarter(q.to_snapshot)}`,
      })),
    ];
    periodGroup.replaceChildren(
      segmented("Period", options, String(periodIndex), (value) => {
        periodIndex = Number(value);
        render();
      }),
    );
  }

  function draw(width: number): Element {
    const data = segments(table());
    const t = table();
    const plot = Plot.plot({
      width,
      height: 200,
      marginLeft: 104,
      style: plotStyle(),
      x: { label: "% of the band's listings with open dates →", domain: [0, 100], grid: true },
      y: { label: null, domain: BANDS.map((b) => BAND_LABELS[b]) },
      color: {
        domain: [...OUTCOMES],
        range: OUTCOMES.map((o) => cssVar(OUTCOME_COLOURS[o])),
        legend: true,
      },
      marks: [
        Plot.barX(data, Plot.stackX({ x: "share", y: "band", fill: "outcome", order: [...OUTCOMES] })),
        Plot.tip(
          data,
          Plot.pointer(
            Plot.stackX({
              x: "share",
              y: "band",
              z: "outcome", // the tip needs the same grouping as the bars to stack identically
              order: [...OUTCOMES],
              title: (d: Segment) => `${d.band} in ${formatQuarter(t.from_snapshot)}\n${d.outcome}: ${formatInt(d.listings)} (${formatPct(d.share)})`,
            }),
          ),
        ),
      ],
    });
    plot.setAttribute(
      "aria-label",
      `Stacked bars: what happened by ${formatQuarter(t.to_snapshot)} to ${CITY_LABELS[city]}'s ${POPULATION} of ${formatQuarter(t.from_snapshot)}, by stay band.`,
    );
    return plot;
  }

  controls.append(
    segmented(
      "City",
      CITIES.map((c) => ({ value: c, label: CITY_LABELS[c] })),
      city,
      (value) => {
        city = value;
        periodIndex = -1;
        renderPeriodControl();
        render();
      },
    ),
    periodGroup,
  );
  renderPeriodControl();
  render = mountChart(chart, draw);
}

export function initExitGap(cities: CityRow[]): void {
  const chart = requireElement("gap-chart");
  const readout = requireElement("gap-readout");
  const rows = CITIES.map((c) => cities.find((row) => row.city === c)).filter((r): r is CityRow => r !== undefined);
  const barcelona = rows.find((r) => r.city === "barcelona");
  if (!barcelona) return;

  mountChart(chart, (width) => {
    const plot = Plot.plot({
      width,
      height: 220,
      marginLeft: 80,
      style: plotStyle(),
      x: { label: "exit gap, percentage points (month-plus minus tourist) →", grid: true, nice: true },
      y: { label: null, domain: rows.map((r) => CITY_LABELS[r.city]) },
      marks: [
        Plot.ruleX([0], { stroke: cssVar("--muted") }),
        Plot.ruleY(rows, {
          y: (r: CityRow) => CITY_LABELS[r.city],
          x1: (r: CityRow) => r.exit_gap.ci_low,
          x2: (r: CityRow) => r.exit_gap.ci_high,
          stroke: (r: CityRow) => (r.city === "barcelona" ? cssVar("--seasonal") : cssVar("--tourist")),
          strokeWidth: 3,
        }),
        Plot.dot(rows, {
          y: (r: CityRow) => CITY_LABELS[r.city],
          x: (r: CityRow) => r.exit_gap.points,
          r: 6,
          fill: (r: CityRow) => (r.city === "barcelona" ? cssVar("--seasonal") : cssVar("--tourist")),
          tip: true,
          title: (r: CityRow) =>
            `${CITY_LABELS[r.city]}: ${r.exit_gap.points > 0 ? "+" : ""}${r.exit_gap.points} points\n95% CI [${r.exit_gap.ci_low}, ${r.exit_gap.ci_high}]`,
        }),
      ],
    });
    plot.setAttribute("aria-label", "Dot chart with 95% confidence intervals: exit gap by city.");
    return plot;
  });

  // The conclusion is computed, not written in: which cities' intervals
  // overlap Barcelona's?
  const others = rows.filter((r) => r.city !== "barcelona");
  const overlaps = (r: CityRow) => r.exit_gap.ci_low <= barcelona.exit_gap.ci_high && r.exit_gap.ci_high >= barcelona.exit_gap.ci_low;
  const similar = others.filter(overlaps).map((r) => CITY_LABELS[r.city]);
  const different = others.filter((r) => !overlaps(r)).map((r) => `${CITY_LABELS[r.city]} (${r.exit_gap.points > 0 ? "+" : ""}${r.exit_gap.points})`);
  const gap = barcelona.exit_gap;
  readout.textContent =
    `Barcelona: month-plus listings were ${gap.points} points more likely to be gone by September than tourist listings (95% CI ${gap.ci_low} to ${gap.ci_high}). ` +
    (similar.length
      ? `${similar.join(", ")} — none of them under the Catalan law — show gaps in the same range. `
      : "No other city shows a gap in the same range. ") +
    (different.length ? `${different.join(", ")} ${different.length === 1 ? "is" : "are"} the exception. ` : "") +
    (similar.length
      ? "So the data does not single out the Catalan seasonal-rent cap: month-plus listings churn faster in most of these cities."
      : "The timing matches the Catalan seasonal-rent cap, but a difference in timing is not proof of a cause.");
}
