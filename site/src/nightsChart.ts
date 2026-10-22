// "Where would you draw the line?" - minimum-stay distribution with a
// movable legal line.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import { CITIES, CITY_LABELS, type City, type CityRow, type NightsRow } from "./data";
import { cssVar, el, formatInt, formatPct, POPULATION, requireElement, segmented } from "./ui";

const MAX_NIGHTS_SHOWN = 60; // longer minimum stays are summarised in the readout
const CHART_HEIGHT = 300;
const NARROW_WIDTH = 520; // below this, axis labels every 10 nights instead of 5

interface Bar {
  nights: number;
  listings: number;
  share: number;
  medianPrice: number | null;
  side: "tourist" | "seasonal";
}

export function initNightsChart(rows: NightsRow[], legalLine: number, cities: CityRow[]): void {
  const chart = requireElement<HTMLDivElement>("nights-chart");
  const controls = requireElement<HTMLDivElement>("nights-controls");
  const readout = requireElement<HTMLParagraphElement>("nights-readout");
  const robustness = requireElement<HTMLParagraphElement>("nights-robustness");

  const roundsFor = (city: City) => [...new Set(rows.filter((r) => r.city === city).map((r) => r.round))];

  let city: City = "barcelona";
  let round = roundsFor(city).at(-1) ?? "";
  let line = legalLine;
  let render = () => {}; // replaced by mountChart below

  function bars(): { shown: Bar[]; total: number; beyond: number } {
    const selected = rows.filter((r) => r.city === city && r.round === round);
    const total = selected.reduce((sum, r) => sum + r.listings, 0);
    const shown = selected
      .filter((r) => r.nights <= MAX_NIGHTS_SHOWN)
      .map((r) => ({
        nights: r.nights,
        listings: r.listings,
        share: (r.listings / total) * 100,
        medianPrice: r.median_price,
        side: r.nights <= line ? ("tourist" as const) : ("seasonal" as const),
      }));
    const beyond = selected.filter((r) => r.nights > MAX_NIGHTS_SHOWN).reduce((sum, r) => sum + r.listings, 0);
    return { shown, total, beyond };
  }

  function draw(width: number): Element {
    const { shown, total, beyond } = bars();
    updateReadout(shown, total, beyond);
    const tickStep = width < NARROW_WIDTH ? 10 : 5;
    const tipText = (d: Bar) =>
      [
        `${d.nights} night${d.nights === 1 ? "" : "s"} minimum`,
        `${formatInt(d.listings)} listings (${formatPct(d.share)})`,
        d.medianPrice === null ? "no prices in this snapshot" : `median asking price €${Math.round(d.medianPrice)}`,
      ].join("\n");

    const plot = Plot.plot({
      width,
      height: CHART_HEIGHT,
      marginLeft: 40,
      marginBottom: 36,
      style: plotStyle(),
      x: {
        label: "minimum stay (nights) →",
        type: "band",
        domain: Array.from({ length: MAX_NIGHTS_SHOWN }, (_, i) => i + 1),
        // Label 1, the line itself, and round numbers that are not so close
        // to the line that the labels collide.
        tickFormat: (n: number) =>
          n === 1 || n === line || (n % tickStep === 0 && Math.abs(n - line) > 2) ? String(n) : "",
        padding: 0.12,
      },
      y: { label: `↑ % of ${POPULATION}`, grid: true, nice: true },
      color: {
        domain: ["tourist", "seasonal"],
        range: [cssVar("--tourist"), cssVar("--seasonal")],
      },
      marks: [
        Plot.barY(shown, { x: "nights", y: "share", fill: "side" }),
        Plot.ruleX([line], {
          x: (n: number) => n,
          dx: width / MAX_NIGHTS_SHOWN / 2,
          stroke: cssVar("--text"),
          strokeDasharray: "4,3",
        }),
        Plot.ruleY([0], { stroke: cssVar("--line") }),
        Plot.tip(shown, Plot.pointerX({ x: "nights", y: "share", title: tipText })),
      ],
    });
    plot.setAttribute(
      "aria-label",
      `Bar chart: share of ${CITY_LABELS[city]} ${POPULATION} by minimum stay, ${round}.`,
    );
    return plot;
  }

  /** The 31+ share under three definitions of the population (latest snapshot). */
  function updateRobustness(): void {
    const check = cities.find((c) => c.city === city)?.availability_sensitivity;
    if (!check) return;
    const { open_dates: open, open_dates_or_reviewed_12m: reviewed, all_listings: all } = check;
    robustness.textContent =
      `Does the population matter? Among listings with a known minimum stay (latest snapshot), the 31+ share is ` +
      `${formatPct(open.month_plus_pct)} for ${POPULATION}, ${formatPct(reviewed.month_plus_pct)} adding listings reviewed in the last 12 months, ` +
      `and ${formatPct(all.month_plus_pct)} for every listing. ` +
      `${formatInt(all.unknown_minimum_stay)} listings have no minimum stay on file and are left out, not counted as short stays.`;
  }

  function updateReadout(shown: Bar[], total: number, beyond: number): void {
    updateRobustness();
    const touristSide = shown.filter((b) => b.side === "tourist").reduce((s, b) => s + b.listings, 0);
    const nearLine = shown.filter((b) => b.nights === line || b.nights === line + 1).reduce((s, b) => s + b.listings, 0);
    readout.replaceChildren(
      document.createTextNode(`${CITY_LABELS[city]}, ${round}: with the line after ${line} nights, `),
      el("span", { class: "tourist" }, formatPct((touristSide / total) * 100)),
      document.createTextNode(` of ${POPULATION} are on the short side and `),
      el("span", { class: "seasonal" }, formatPct(((total - touristSide) / total) * 100)),
      document.createTextNode(
        ` on the long side${beyond ? ` (${formatInt(beyond)} ask more than ${MAX_NIGHTS_SHOWN} nights)` : ""}. ` +
          `${formatPct((nearLine / total) * 100)} sit within one night of the line (${line} or ${line + 1}).`,
      ),
    );
  }

  const roundGroup = el("div");
  function renderRoundControl(): void {
    roundGroup.replaceChildren(
      segmented(
        "Snapshot",
        roundsFor(city).map((r) => ({ value: r, label: r })),
        round,
        (value) => {
          round = value;
          render();
        },
      ),
    );
  }

  const sliderGroup = el("div", { class: "control-group wide" });
  const sliderLabel = el("label", { class: "control-label", for: "line-slider" }, "Draw the line after … nights");
  const slider = el("input", {
    id: "line-slider",
    type: "range",
    min: "1",
    max: String(MAX_NIGHTS_SHOWN - 1),
    step: "1",
    value: String(line),
  });
  const output = el("output", { for: "line-slider" }, `${line}`);
  slider.addEventListener("input", () => {
    line = Number(slider.value);
    output.textContent = `${line}`;
    render();
  });
  const sliderRow = el("div", { class: "slider-row" });
  sliderRow.append(slider, output);
  sliderGroup.append(sliderLabel, sliderRow);

  controls.append(
    segmented(
      "City",
      CITIES.map((c) => ({ value: c, label: CITY_LABELS[c] })),
      city,
      (value) => {
        city = value;
        const rounds = roundsFor(city);
        if (!rounds.includes(round)) round = rounds.at(-1) ?? "";
        renderRoundControl();
        render();
      },
    ),
    roundGroup,
    sliderGroup,
  );
  renderRoundControl();
  render = mountChart(chart, draw);
}
