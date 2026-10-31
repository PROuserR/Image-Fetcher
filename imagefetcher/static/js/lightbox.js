// Full-screen preview: arrows / swipe to navigate, Esc to close, focus is trapped while open.
import { $, $$ } from "./dom.js";
import { icon } from "./icons.js";
import { state, isInline } from "./state.js";
import { proxyUrl, downloadHref } from "./api.js";
import { metaLabel } from "./format.js";
import { toggle } from "./selection.js";
import { visibleOrder } from "./filters.js";
import { copyUrl } from "./actions.js";

const els = {
  root: $("#lightbox"), wrap: $("#lb-imgwrap"), img: $("#lb-img"), name: $("#lb-name"), meta: $("#lb-meta"),
  select: $("#lb-select"), copy: $("#lb-copy"), download: $("#lb-download"), open: $("#lb-open"),
  close: $("#lb-close"), prev: $("#lb-prev"), next: $("#lb-next")
};
let opener = null;

function render() {
  const img = state.images[state.lbIndex];
  if (!img) return;
  els.wrap.dataset.loading = "true";
  els.img.src = proxyUrl(img);
  els.img.alt = img.name;
  els.name.textContent = img.name;
  els.name.title = img.name;
  els.meta.textContent = metaLabel(img);
  els.select.textContent = state.selected.has(img.i) ? "✓ Selected" : "Select";
  els.download.href = downloadHref(img);
  els.download.setAttribute("download", img.name);
  els.open.hidden = els.copy.hidden = isInline(img);
  if (!isInline(img)) els.open.href = img.url;

  // Warm the cache for the neighbours so stepping feels instant.
  const order = visibleOrder();
  const pos = order.indexOf(img.i);
  [order[pos + 1], order[pos - 1]].forEach(n => { if (n != null) new Image().src = proxyUrl(state.images[n]); });
}

export function openLightbox(i) {
  opener = document.activeElement;
  state.lbIndex = i;
  render();
  els.root.hidden = false;
  document.body.classList.add("noscroll");
  els.close.focus();
}

function close() {
  els.root.hidden = true;
  state.lbIndex = -1;
  els.img.removeAttribute("src");
  document.body.classList.remove("noscroll");
  if (opener && opener.focus) opener.focus();
}

function step(dir) {
  const order = visibleOrder();
  const pos = order.indexOf(state.lbIndex);
  if (pos < 0 || order.length < 2) return;
  state.lbIndex = order[(pos + dir + order.length) % order.length];
  render();
}

function trapFocus(e) {
  const focusable = $$("button, a[href]", els.root).filter(el => !el.hidden && el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

export function initLightbox() {
  els.prev.append(icon("left"));
  els.next.append(icon("right"));
  els.close.addEventListener("click", close);
  els.prev.addEventListener("click", () => step(-1));
  els.next.addEventListener("click", () => step(1));
  els.select.addEventListener("click", () => toggle(state.lbIndex));
  els.copy.addEventListener("click", () => copyUrl(state.images[state.lbIndex]));
  els.root.addEventListener("click", e => { if (e.target === els.root) close(); });
  els.img.addEventListener("load", () => {
    els.wrap.dataset.loading = "false";
    const img = state.images[state.lbIndex];
    if (img && !img.w) { img.w = els.img.naturalWidth; img.h = els.img.naturalHeight; els.meta.textContent = metaLabel(img); }
  });
  els.img.addEventListener("error", () => { els.wrap.dataset.loading = "false"; });

  document.addEventListener("selection:changed", () => { if (!els.root.hidden) render(); });
  document.addEventListener("keydown", e => {
    if (els.root.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.key === "ArrowRight") step(1);
    else if (e.key === "Tab") trapFocus(e);
  });

  // Swipe left/right on touch screens.
  let x0 = 0, y0 = 0;
  els.wrap.addEventListener("touchstart", e => { x0 = e.changedTouches[0].clientX; y0 = e.changedTouches[0].clientY; }, { passive: true });
  els.wrap.addEventListener("touchend", e => {
    const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1);
  }, { passive: true });
}
