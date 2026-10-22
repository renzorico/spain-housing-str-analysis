// Shared plumbing for Observable Plot charts: redraw on width or theme
// change, and the theme-aware base style every chart uses.
import { cssVar, onThemeChange } from "./ui";

export const MIN_CHART_WIDTH = 300;

/** Base `style` option for Plot, following the CSS theme tokens. */
export function plotStyle(): Record<string, string> {
  return { background: "transparent", color: cssVar("--text"), fontSize: "12px" };
}

/**
 * Draw a chart into `container` now, and again whenever its width changes
 * or the colour scheme flips. Returns a function to force a redraw after
 * the caller's own state changes (toggles, sliders).
 */
export function mountChart(container: HTMLElement, draw: (width: number) => Element): () => void {
  const render = () => {
    container.replaceChildren(draw(Math.max(MIN_CHART_WIDTH, container.clientWidth)));
  };
  // Redraw only on a real width change, so a redraw cannot trigger
  // another resize callback.
  let lastWidth = container.clientWidth;
  new ResizeObserver(() => {
    if (container.clientWidth === lastWidth) return;
    lastWidth = container.clientWidth;
    render();
  }).observe(container);
  onThemeChange(render);
  render();
  return render;
}
