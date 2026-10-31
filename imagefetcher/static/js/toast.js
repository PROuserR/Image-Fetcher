import { $, h } from "./dom.js";

export function toast(message, type = "info") {
  const el = h("div", { class: `toast ${type === "error" ? "error" : ""}` }, message);
  $("#toasts").append(el);
  setTimeout(() => el.remove(), 3600);
}
