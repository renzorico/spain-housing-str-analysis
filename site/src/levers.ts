// "The rules, one by one": a timeline and one card per policy lever.
// Rule text, laws and dates come from src/config.py via meta.json. The
// "what the data shows" lines are computed from the exported data, so they
// cannot drift from the numbers elsewhere on the page.
import * as Plot from "@observablehq/plot";

import { mountChart, plotStyle } from "./charts";
import { CITIES, CITY_LABELS, type BarcelonaTrend, type CityRow, type Meta, type Register, type RentRow } from "./data";
import { cssVar, el, formatCalendarQuarter, formatInt, formatPct, formatQuarter, POPULATION, requireElement } from "./ui";

const TIMELINE_START = "2023-09-01";
const TIMELINE_END = "2029-03-01";

interface Inputs {
  meta: Meta;
  register: Register;
  rents: RentRow[];
  trends: BarcelonaTrend[];
  cities: CityRow[];
}

function signed(value: number): string {
  return `${value > 0 ? "+" : ""}${value}%`;
}

function dataShows(id: string, { meta, register, rents, trends, cities }: Inputs): string {
  switch (id) {
    case "tourist_licence_phase_out": {
      const latest = register.match.at(-1);
      const totals = Object.values(register.totals);
      if (!latest || totals.length === 0) return "";
      return (
        `The register holds ${formatInt(Math.min(...totals))}–${formatInt(Math.max(...totals))} licensed flats in every published quarter: ` +
        `no decline yet. ${formatPct(latest.match_register_pct, 0)} of licence numbers shown on Airbnb match it, ` +
        `and only ${formatPct(latest.register_visible_pct, 0)} of registered flats appear on Airbnb with their number.`
      );
    }
    case "rent_cap": {
      const capStart = meta.policy_levers.rent_cap?.applies_from;
      if (!capStart) return "";
      const withChange = rents.filter((r): r is RentRow & { yoy_pct: number } => r.yoy_pct !== null);
      // The quarter the cap started in counts as "before": it began mid-March.
      const before = withChange.filter((r) => r.quarter_start <= capStart).at(-1);
      const after = withChange.filter((r) => r.quarter_start > capStart);
      const lowest = after.reduce<(typeof after)[number] | undefined>((min, r) => (!min || r.yoy_pct < min.yoy_pct ? r : min), undefined);
      const latest = withChange.at(-1);
      if (!before || !lowest || !latest) return "";
      const q = formatCalendarQuarter;
      return (
        `New-lease rents were rising ${signed(before.yoy_pct)} a year just before the cap (${q(before.quarter_start)}), ` +
        `fell to ${signed(lowest.yoy_pct)} (${q(lowest.quarter_start)}), and were ${signed(latest.yoy_pct)} in ${q(latest.quarter_start)} ` +
        `(€${formatInt(Math.round(latest.avg_rent))} a month).`
      );
    }
    case "seasonal_rentals": {
      const first = trends[0];
      const second = trends[1];
      const last = trends.at(-1);
      const shareIn = (city: string) => cities.find((c) => c.city === city)?.rounds["Sep 2026"]?.share_month_plus;
      const barcelona = shareIn("barcelona");
      const others = CITIES.filter((c) => c !== "barcelona")
        .map((c) => shareIn(c))
        .filter((v): v is number => v !== undefined);
      const clearGapCities = cities.filter((c) => c.exit_gap.ci_low > 0).map((c) => CITY_LABELS[c.city]);
      if (!first || !second || !last || barcelona === undefined || others.length === 0) return "";
      return (
        `${formatPct(barcelona, 0)} of Barcelona's ${POPULATION} ask 31+ nights, vs ${Math.round(Math.min(...others))}–${Math.round(Math.max(...others))}% in ${CITIES.filter((c) => c !== "barcelona").map((c) => CITY_LABELS[c]).join(", ")}. ` +
        `Seasonal-band listings went from ${formatInt(first.bands.seasonal)} (${formatQuarter(first.snapshot)}) to ${formatInt(second.bands.seasonal)} (${formatQuarter(second.snapshot)}) and ${formatInt(last.bands.seasonal)} (${formatQuarter(last.snapshot)}). ` +
        `Month-plus listings were clearly more likely than shorter-stay ones to be absent from the later scrape in ${clearGapCities.length} of 5 cities (${clearGapCities.join(", ")}; host-account intervals above zero), and Barcelona's gap cannot be told apart from any other city's.`
      );
    }
    case "owners_vote_catalonia":
    case "owners_approval_spain":
      return "No direct measure. This rule acts building by building, and listing data cannot see it.";
    default:
      return "";
  }
}

interface Span {
  row: string;
  start: Date;
  end: Date;
  label: string;
}

function day(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}

const DATA_ROW = "Data on this page";
const LATER_ROW = "Later events";

function timelineSpans(meta: Meta): { spans: Span[]; points: Span[] } {
  const timelineStart = day(TIMELINE_START);
  const timelineEnd = day(TIMELINE_END);
  const clamp = (date: Date) => (date < timelineStart ? timelineStart : date);
  const spans: Span[] = Object.values(meta.policy_levers).map((lever) => ({
    row: lever.timeline_label,
    start: clamp(day(lever.applies_from)),
    end: lever.deadline ? day(lever.deadline) : timelineEnd,
    label: lever.deadline ? `from ${lever.applies_from}; deadline ${lever.deadline}` : `in force from ${lever.applies_from}`,
  }));
  const [first, last] = meta.observation_window;
  spans.push({ row: DATA_ROW, start: day(first), end: day(last), label: `snapshots ${first} to ${last}` });
  const points: Span[] = [
    ...meta.post_observation_developments.map((item) => ({
      row: LATER_ROW,
      start: day(item.date),
      end: day(item.date),
      label: `${item.title}: ${item.date}`,
    })),
    ...Object.entries(meta.context_events).map(([id, date]) => ({
      row: LATER_ROW,
      start: day(date),
      end: day(date),
      label: `${id.replace("_", " ")}: ${date}`,
    })),
  ];
  return { spans, points };
}

export function initLevers(inputs: Inputs): void {
  const { meta } = inputs;
  const { spans, points } = timelineSpans(meta);
  const rows = [...spans.map((s) => s.row), LATER_ROW];

  mountChart(requireElement("timeline-chart"), (width) => {
    const narrow = width < 560;
    const plot = Plot.plot({
      width,
      height: 40 + rows.length * 34,
      marginLeft: 158,
      style: plotStyle(),
      x: { type: "utc", domain: [day(TIMELINE_START), day(TIMELINE_END)], label: null, ticks: narrow ? 4 : 7 },
      y: { domain: rows, label: null },
      marks: [
        Plot.ruleX([new Date()], { stroke: cssVar("--muted"), strokeDasharray: "2,3" }),
        Plot.barX(spans, {
          x1: "start",
          x2: "end",
          y: "row",
          fill: (s: Span) => (s.row === DATA_ROW ? cssVar("--seasonal") : cssVar("--tourist")),
          fillOpacity: 0.75,
          insetTop: 9,
          insetBottom: 9,
          tip: true,
          title: (s: Span) => `${s.row}\n${s.label}`,
        }),
        Plot.dot(points, { x: "start", y: "row", r: 6, fill: cssVar("--cat-4"), tip: true, title: "label" }),
      ],
    });
    plot.setAttribute("aria-label", "Timeline: when each selected housing rule applies, the period covered by this data, and later events including elections.");
    return plot;
  });

  requireElement("lever-cards").replaceChildren(
    ...Object.entries(meta.policy_levers).map(([id, lever]) => {
      const card = el("article", { class: "card" });
      const facts = el("dl");
      const add = (term: string, text: string) => {
        if (text) facts.append(el("dt", {}, term), el("dd", {}, text));
      };
      add("Applies to", `${lever.jurisdiction}. Cities here: ${lever.applies_to.map((c) => CITY_LABELS[c]).join(", ")}.`);
      add("What it says", lever.rule);
      if (lever.exceptions.length > 0) {
        facts.append(el("dt", {}, "Exceptions and conditions"));
        const list = el("ul");
        for (const exception of lever.exceptions) list.append(el("li", {}, exception));
        const wrapper = el("dd");
        wrapper.append(list);
        facts.append(wrapper);
      }
      add("Since", lever.deadline ? `${lever.applies_from}; deadline ${lever.deadline}` : lever.applies_from);
      add("Status", `${lever.status} (checked ${lever.status_checked_on})`);
      add("Details", lever.notes);
      add("What this data shows", dataShows(id, inputs));
      add("What this data cannot show", lever.data_limits);
      card.append(el("h3", {}, lever.title), el("p", { class: "law" }, lever.law), facts);
      const links = el("p", { class: "card-links" });
      lever.sources.forEach((source, index) => {
        if (index > 0) links.append(document.createTextNode(" · "));
        links.append(el("a", { href: source.url, rel: "noopener" }, source.label));
      });
      card.append(links);
      return card;
    }),
  );

  // Developments after the last snapshot: context, never an explanation.
  const later = requireElement("later-developments");
  later.replaceChildren(
    ...meta.post_observation_developments.map((item) => {
      const card = el("article", { class: "card" });
      card.append(
        el("h3", {}, item.title),
        el("p", { class: "law" }, `After the observation window · ${item.date}`),
        el("p", {}, item.summary),
        el("p", { class: "note" }, item.note),
        el("a", { href: item.url, rel: "noopener" }, "Official text"),
      );
      return card;
    }),
  );
}
