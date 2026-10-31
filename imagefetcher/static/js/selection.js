import { $ } from "./dom.js";
import { state } from "./state.js";

const els = {
  count: $("#sel-count"), zip: $("#zip-btn"), all: $("#select-all"), none: $("#select-none")
};

export function updateBar() {
  const n = state.selected.size;
  els.count.textContent = n;
  els.zip.disabled = n === 0;
  $(".label", els.zip).textContent = n ? `Download ZIP (${n})` : "Download ZIP";
}

export function setSelected(i, on) {
  const img = state.images[i];
  if (on) state.selected.add(i); else state.selected.delete(i);
  img.card.classList.toggle("selected", on);
  $(".check", img.card).setAttribute("aria-checked", String(on));
}

const announce = () => document.dispatchEvent(new CustomEvent("selection:changed"));

export function toggle(i) {
  setSelected(i, !state.selected.has(i));
  updateBar();
  announce();
}

export function clearSelection() {
  [...state.selected].forEach(i => setSelected(i, false));
  updateBar();
  announce();
}

export function resetSelection() {
  state.selected.clear();
  updateBar();
}

export function initSelection() {
  els.all.addEventListener("click", () => {
    state.images.forEach(img => { if (!img.card.hidden) setSelected(img.i, true); });
    updateBar();
    announce();
  });
  els.none.addEventListener("click", clearSelection);
}
