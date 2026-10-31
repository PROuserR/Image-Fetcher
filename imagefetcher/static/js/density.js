// Thumbnail size (S / M / L), remembered between visits.
import { $$ } from "./dom.js";
import { store } from "./storage.js";

const VALUES = ["compact", "comfortable", "large"];

export function initDensity(group, grid) {
  const apply = value => {
    grid.dataset.density = value;
    $$("button", group).forEach(b => b.setAttribute("aria-pressed", String(b.dataset.density === value)));
    store.set("density", value);
  };
  group.addEventListener("click", e => {
    const btn = e.target.closest("button[data-density]");
    if (btn) apply(btn.dataset.density);
  });
  const saved = store.get("density");
  apply(VALUES.includes(saved) ? saved : "comfortable");
}
