import { $, h } from "./dom.js";

export function showStatus(kind, emoji, title, text) {
  const el = $("#status");
  el.className = `status ${kind}`;
  el.replaceChildren(h("div", { class: "big" }, emoji), h("h2", {}, title), h("p", {}, text));
}

export function clearStatus() {
  const el = $("#status");
  el.className = "status";
  el.replaceChildren();
}

export const statusIsError = () => $("#status").classList.contains("error");
