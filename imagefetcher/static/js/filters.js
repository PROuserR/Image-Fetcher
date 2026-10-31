// Filtering and sorting. Cards are shown/hidden and re-ordered with CSS `order`,
// so nothing is rebuilt (thumbnails don't reload and the lightbox keeps working).
import { $, h } from "./dom.js";
import { state } from "./state.js";

const side = img => Math.max(img.w || 0, img.h || 0);
const sorters = {
  page: (a, b) => a.i - b.i,
  size: (a, b) => side(b) - side(a) || a.i - b.i,
  name: (a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }) || a.i - b.i
};

export function applyFilters() {
  const q = state.query.trim().toLowerCase();
  let shown = 0;
  for (const img of state.images) {
    const textOk = !q || img.name.toLowerCase().includes(q) ||
      (!img.url.startsWith("data:") && img.url.toLowerCase().includes(q));
    const sizeOk = !state.minSize || !side(img) || side(img) >= state.minSize; // unknown size passes
    const ok = state.activeExts.has(img.ext) && textOk && sizeOk;
    img.card.hidden = !ok;
    if (ok) shown++;
  }
  [...state.images].sort(sorters[state.sort]).forEach((img, rank) => { img.card.style.order = rank; });

  $("#count").textContent = `Showing ${shown} of ${state.images.length}`;
  document.dispatchEvent(new CustomEvent("filters:applied", { detail: { shown, total: state.images.length } }));
  return shown;
}

// Indexes of visible images in on-screen order (used by lightbox navigation).
export const visibleOrder = () =>
  state.images.filter(img => !img.card.hidden).sort(sorters[state.sort]).map(img => img.i);

let queued = false;
export function scheduleFilter() {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; applyFilters(); });
}

export function resetFilters() {
  state.query = "";
  state.minSize = 0;
  state.sort = "page";
  $("#search").value = "";
  $("#min-size").value = "0";
  $("#sort").value = "page";
}

export function buildChips() {
  const counts = {};
  state.images.forEach(img => { counts[img.ext] = (counts[img.ext] || 0) + 1; });
  state.activeExts = new Set(Object.keys(counts));
  const order = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  $("#chips").replaceChildren(...order.map(ext => {
    const chip = h("button", { class: "chip", type: "button", "aria-pressed": "true" },
      ext === "other" ? "Other" : ext.toUpperCase(), h("small", {}, String(counts[ext])));
    chip.addEventListener("click", () => {
      const on = chip.getAttribute("aria-pressed") !== "true";
      chip.setAttribute("aria-pressed", String(on));
      if (on) state.activeExts.add(ext); else state.activeExts.delete(ext);
      applyFilters();
    });
    return chip;
  }));
}

// Thumbnails are lazy-loaded, so an image's pixel size is unknown until it loads.
// Sorting or filtering by size needs every size, so load them all on demand.
function loadAllThumbnails() {
  state.images.forEach(img => { if (img.thumb) img.thumb.loading = "eager"; });
}

export function initFilters() {
  $("#search").addEventListener("input", e => { state.query = e.target.value; applyFilters(); });
  $("#min-size").addEventListener("change", e => {
    state.minSize = Number(e.target.value);
    if (state.minSize) loadAllThumbnails();
    applyFilters();
  });
  $("#sort").addEventListener("change", e => {
    state.sort = e.target.value;
    if (state.sort === "size") loadAllThumbnails();
    applyFilters();
  });

  // Filters are always open on wide screens and collapsible on phones.
  const panel = $("#filter-panel");
  const wide = window.matchMedia("(min-width: 768px)");
  const sync = () => { panel.open = wide.matches; };
  sync();
  if (wide.addEventListener) wide.addEventListener("change", sync);
}
