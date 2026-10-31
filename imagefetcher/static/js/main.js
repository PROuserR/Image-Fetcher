// App entry point: wires the modules together and runs the scan flow.
import { $, h } from "./dom.js";
import { state } from "./state.js";
import { scanPage } from "./api.js";
import { store } from "./storage.js";
import { toast } from "./toast.js";
import { initTheme } from "./theme.js";
import { initDensity } from "./density.js";
import { showStatus, clearStatus, statusIsError } from "./status.js";
import { renderGrid } from "./grid.js";
import { applyFilters, buildChips, initFilters, resetFilters } from "./filters.js";
import { initSelection, resetSelection } from "./selection.js";
import { initLightbox } from "./lightbox.js";
import { initZip } from "./zip.js";

const els = {
  form: $("#scan-form"), url: $("#url"), scanBtn: $("#scan-btn"), extras: $("#extras"),
  toolbar: $("#toolbar"), pageTitle: $("#page-title"), grid: $("#grid"), bar: $("#actionbar")
};

function setScanning(on) {
  els.scanBtn.disabled = on;
  $(".spinner", els.scanBtn).hidden = !on;
  $(".label", els.scanBtn).textContent = on ? "Fetching…" : "Fetch images";
}

const hostOf = url => { try { return new URL(url).hostname.replace(/^www\./, ""); } catch (_) { return "images"; } };

async function scan(rawUrl) {
  const url = rawUrl.trim();
  if (!url) { els.url.focus(); return; }

  setScanning(true);
  clearStatus();
  els.toolbar.hidden = true;
  els.bar.hidden = true;
  els.grid.replaceChildren(...Array.from({ length: 8 }, () => h("div", { class: "skeleton" })));

  try {
    const data = await scanPage(url, els.extras.checked);
    state.page = data.page;
    state.host = hostOf(data.page);
    state.images = data.images.map((img, i) => ({ ...img, i }));
    resetSelection();
    resetFilters();
    els.pageTitle.textContent = data.title ? `“${data.title}” · ${state.host}` : state.host;

    if (!state.images.length) {
      els.grid.replaceChildren();
      showStatus("", "🔍", "No images found",
        "This page may load its images with JavaScript, which this tool can't run. Try another page.");
      return;
    }
    if (data.truncated) toast("Showing the first 500 images only.");

    renderGrid(els.grid, state.images);
    buildChips();
    els.toolbar.hidden = false;
    els.bar.hidden = false;
    applyFilters();
    history.replaceState(null, "", `?url=${encodeURIComponent(url)}`);
    els.grid.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    els.grid.replaceChildren();
    showStatus("error", "⚠️", "Couldn't fetch that page", err.message);
  } finally {
    setScanning(false);
  }
}

/* ---------- boot ---------- */
initTheme($("#theme"));
initDensity($("#density"), els.grid);
initFilters();
initSelection();
initLightbox();
initZip($("#zip-btn"));

els.extras.checked = store.get("extras", "1") === "1";
els.extras.addEventListener("change", () => store.set("extras", els.extras.checked ? "1" : "0"));
els.form.addEventListener("submit", e => { e.preventDefault(); scan(els.url.value); });

document.addEventListener("filters:applied", ({ detail }) => {
  if (detail.total && detail.shown === 0) {
    showStatus("", "🧹", "No images match your filters", "Try clearing the search or turning on more file types.");
  } else if (!statusIsError()) {
    clearStatus();
  }
});

const initial = new URLSearchParams(location.search).get("url");
if (initial) {
  els.url.value = initial;
  scan(initial);
} else {
  showStatus("", "🖼️", "Paste a link to get started", "Any public webpage works: a blog post, a product page, a gallery.");
}
