// Small, framework-free UI helpers shared by the sections.

export const formatInt = new Intl.NumberFormat("en-GB").format;

export function formatPct(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

export function formatQuarter(snapshot: string): string {
  // en-US gives "Sep 2026", matching the labels in the exported data
  // (en-GB would say "Sept 2026").
  return new Date(`${snapshot}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

/** Read a CSS custom property so charts and the map follow the theme. */
export function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Record<string, string> = {},
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

export function requireElement<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing #${id} in index.html`);
  return node as T;
}

export interface Option<V extends string> {
  value: V;
  label: string;
}

/** A labelled row of toggle buttons; calls onChange with the chosen value. */
export function segmented<V extends string>(
  label: string,
  options: Option<V>[],
  initial: V,
  onChange: (value: V) => void,
): HTMLElement {
  const group = el("div", { class: "control-group" });
  const id = `seg-${label.toLowerCase().replace(/\W+/g, "-")}`;
  group.append(el("span", { class: "control-label", id }, label));
  const row = el("div", { class: "segmented", role: "group", "aria-labelledby": id });
  const buttons = options.map((option) => {
    const button = el("button", { type: "button", "aria-pressed": String(option.value === initial) }, option.label);
    button.addEventListener("click", () => {
      for (const other of buttons) other.setAttribute("aria-pressed", String(other === button));
      onChange(option.value);
    });
    row.append(button);
    return button;
  });
  group.append(row);
  // On phones the row scrolls sideways: bring the selected button into view
  // once it is laid out (scrollLeft, not scrollIntoView, so the page stays put).
  requestAnimationFrame(() => {
    const selected = buttons.find((b) => b.getAttribute("aria-pressed") === "true");
    if (selected && row.scrollWidth > row.clientWidth) row.scrollLeft = selected.offsetLeft - row.offsetLeft;
  });
  return group;
}

/** Re-run a callback when the colour scheme flips, so SVG/canvas colours update. */
export function onThemeChange(callback: () => void): void {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", callback);
}
