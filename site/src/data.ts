// Types and loaders for the JSON written by scripts/export_site_data.py.
// Paths are relative so the build works under any GitHub Pages subpath.

export const CITIES = ["barcelona", "madrid", "valencia", "malaga", "sevilla"] as const;
export type City = (typeof CITIES)[number];

export const CITY_LABELS: Record<City, string> = {
  barcelona: "Barcelona",
  madrid: "Madrid",
  valencia: "Valencia",
  malaga: "Málaga",
  sevilla: "Sevilla",
};

export interface Source {
  title: string;
  url: string;
  licence: string;
}

export interface PolicyLever {
  rule: string;
  law: string;
  applies_from: string;
  deadline: string | null;
  source: string;
  notes: string;
}

export interface Meta {
  generated: string;
  snapshots: Record<City, string[]>;
  policy_levers: Record<string, PolicyLever>;
  context_events: Record<string, string>;
  max_tourist_nights: number;
  sources: Source[];
  caveats: string[];
}

/** One quarter's active Barcelona listings, as parallel arrays. */
export interface Points {
  legend: {
    band: string[];
    licence: string[];
    room: string[];
    host_size: string[];
  };
  lat: number[];
  lon: number[];
  band: number[];
  licence: number[];
  room: number[];
  host_size: number[];
  nights: number[];
  price: (number | null)[];
}

export interface NightsRow {
  city: City;
  snapshot: string;
  round: string;
  nights: number;
  listings: number;
  median_price: number | null;
}

export interface SnapshotSummary {
  listings: number;
  active: number;
  share_31_nights: number;
  share_month_plus: number;
  share_tourist_licence: number;
  share_nrua_seasonal: number;
  share_professional: number;
  share_entire_home: number;
  median_price: number | null;
}

export interface CityRow {
  city: City;
  rounds: Record<string, SnapshotSummary>;
  exit_gap: { points: number; ci_low: number; ci_high: number };
  top_host_share: Record<string, number>;
}

export interface RegisterMatch {
  snapshot: string;
  listings_showing_number: number;
  distinct_numbers: number;
  match_register_pct: number;
  register_visible_pct: number;
  numbers_on_2plus_listings: number;
}

export interface Register {
  register_quarter: string;
  totals: Record<string, number>;
  match: RegisterMatch[];
}

async function loadJson<T>(file: string): Promise<T> {
  const response = await fetch(`data/${file}`);
  if (!response.ok) {
    throw new Error(`Could not load data/${file} (HTTP ${response.status})`);
  }
  return (await response.json()) as T;
}

export const loadMeta = () => loadJson<Meta>("meta.json");
export const loadNights = () => loadJson<NightsRow[]>("minimum_nights.json");
export const loadCities = () => loadJson<CityRow[]>("cities.json");
export const loadRegister = () => loadJson<Register>("register.json");

// Map files are ~400 kB each, so they are fetched on demand and cached.
const pointsCache = new Map<string, Promise<Points>>();
export function loadPoints(snapshot: string): Promise<Points> {
  let cached = pointsCache.get(snapshot);
  if (!cached) {
    cached = loadJson<Points>(`barcelona_points_${snapshot}.json`);
    pointsCache.set(snapshot, cached);
  }
  return cached;
}
