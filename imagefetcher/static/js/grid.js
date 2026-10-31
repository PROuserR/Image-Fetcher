// Builds the image cards.
import { h } from "./dom.js";
import { icon } from "./icons.js";
import { proxyUrl, downloadHref } from "./api.js";
import { typeLabel, metaLabel } from "./format.js";
import { toggle } from "./selection.js";
import { openLightbox } from "./lightbox.js";
import { copyUrl } from "./actions.js";
import { scheduleFilter } from "./filters.js";

function buildCard(img) {
  const meta = h("span", { class: "meta" }, typeLabel(img));
  const thumb = h("img", { src: proxyUrl(img), alt: img.name, loading: "lazy", decoding: "async" });
  const card = h("article", { class: "card" });

  thumb.addEventListener("load", () => {
    img.w = thumb.naturalWidth;
    img.h = thumb.naturalHeight;
    if (img.w) meta.textContent = metaLabel(img);
    scheduleFilter(); // size filter / size sort may now apply
  });
  thumb.addEventListener("error", () => card.classList.add("broken"));

  const check = h("button", {
    class: "check", type: "button", role: "checkbox", "aria-checked": "false", "aria-label": `Select ${img.name}`,
    onclick: e => { e.stopPropagation(); toggle(img.i); }
  }, icon("check"));

  const view = h("button", {
    class: "thumb", type: "button", "aria-label": `Preview ${img.name}`, onclick: () => openLightbox(img.i)
  }, thumb, h("span", { class: "fallback" }, "Preview unavailable"));

  const copyBtn = h("button", {
    class: "btn-icon", type: "button", title: "Copy image URL", "aria-label": "Copy image URL",
    onclick: () => copyUrl(img)
  }, icon("copy"));
  const dlLink = h("a", {
    class: "btn-icon", href: downloadHref(img), download: img.name, title: "Download this image", "aria-label": "Download this image"
  }, icon("download"));

  card.append(
    check, view,
    h("div", { class: "info" },
      h("div", { class: "name", title: img.name }, img.name),
      h("div", { class: "row" }, meta, h("div", { class: "mini" }, copyBtn, dlLink)))
  );
  img.card = card;
  img.thumb = thumb;
  return card;
}

export function renderGrid(container, images) {
  container.replaceChildren(...images.map(buildCard));
}
