// Small DOM helpers. h() builds elements safely: text is never parsed as HTML.
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [key, val] of Object.entries(props)) {
    if (key === "class") el.className = val;
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), val);
    else if (val === true) el.setAttribute(key, "");
    else if (val !== false && val != null) el.setAttribute(key, val);
  }
  el.append(...kids);
  return el;
}
