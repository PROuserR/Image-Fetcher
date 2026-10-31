import { icon } from "./icons.js";
import { store } from "./storage.js";

export function initTheme(button) {
  const root = document.documentElement;
  const apply = theme => {
    root.dataset.theme = theme;
    button.replaceChildren(icon(theme === "dark" ? "sun" : "moon"));
    store.set("theme", theme);
  };
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const saved = store.get("theme");
  apply(saved === "dark" || saved === "light" ? saved : prefersDark ? "dark" : "light");
  button.addEventListener("click", () => apply(root.dataset.theme === "dark" ? "light" : "dark"));
}
