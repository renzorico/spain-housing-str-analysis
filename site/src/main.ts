import "./styles.css";

import { CITIES, CITY_LABELS, loadCities, loadMeta, loadNights, loadRegister, type CityRow, type Meta, type Register } from "./data";
import { initNightsChart } from "./nightsChart";
import { el, formatPct, requireElement } from "./ui";

const LATEST_ROUND = "Sep 2026";

function renderHeroStats(cities: CityRow[], register: Register): void {
  const latest = (city: string) => cities.find((c) => c.city === city)?.rounds[LATEST_ROUND];
  const barcelona = latest("barcelona");
  const others = CITIES.filter((c) => c !== "barcelona")
    .map((c) => latest(c)?.share_month_plus)
    .filter((v): v is number => v !== undefined);
  const match = register.match.at(-1);
  if (!barcelona || others.length === 0 || !match) return;

  const tiles: [string, string][] = [
    [formatPct(barcelona.share_month_plus, 0), `of Barcelona's active listings ask for 31 nights or more (${LATEST_ROUND})`],
    [
      `${Math.round(Math.min(...others))}–${Math.round(Math.max(...others))}%`,
      `in ${CITIES.filter((c) => c !== "barcelona").map((c) => CITY_LABELS[c]).join(", ")}`,
    ],
    [formatPct(match.match_register_pct, 0), "of tourist-licence numbers shown on Airbnb match the official register"],
  ];
  requireElement("hero-stats").replaceChildren(
    ...tiles.map(([value, label]) => {
      const tile = el("div", { class: "stat" });
      tile.append(el("strong", {}, value), el("span", {}, label));
      return tile;
    }),
  );
}

function renderFooter(meta: Meta): void {
  requireElement("sources").replaceChildren(
    ...meta.sources.map((source) => {
      const item = el("li");
      item.append(el("a", { href: source.url, rel: "noopener" }, source.title), document.createTextNode(` (${source.licence})`));
      return item;
    }),
  );
  requireElement("caveats").replaceChildren(...meta.caveats.map((text) => el("li", {}, text)));
}

function showError(error: unknown): void {
  const message = error instanceof Error ? error.message : String(error);
  document.querySelector("main")?.prepend(el("p", { class: "note", role: "alert" }, `Could not load the data: ${message}`));
}

// MapLibre is most of the JavaScript, so it is only downloaded when the
// reader scrolls near the map.
const MAP_PRELOAD_MARGIN = "600px";

function loadMapWhenNear(snapshots: string[]): void {
  const section = requireElement("map-section");
  const load = () => import("./map").then(({ initMap }) => initMap(snapshots)).catch(showError);
  // Already close (e.g. a link straight to #map-section): load now rather
  // than wait for the observer's first callback.
  if (section.getBoundingClientRect().top < window.innerHeight + parseInt(MAP_PRELOAD_MARGIN, 10)) {
    void load();
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      observer.disconnect();
      void load();
    },
    { rootMargin: MAP_PRELOAD_MARGIN },
  );
  observer.observe(section);
}

async function main(): Promise<void> {
  const [meta, nights, cities, register] = await Promise.all([loadMeta(), loadNights(), loadCities(), loadRegister()]);
  renderHeroStats(cities, register);
  renderFooter(meta);
  initNightsChart(nights, meta.max_tourist_nights);
  loadMapWhenNear(meta.snapshots.barcelona);
}

main().catch(showError);
