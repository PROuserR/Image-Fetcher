// Single shared state object. Image records look like:
// { i, url, name, ext, w, h, card }   (w/h/card are filled in client-side)
export const state = {
  images: [],
  selected: new Set(),
  page: "",
  host: "images",
  activeExts: new Set(),
  query: "",
  minSize: 0,
  sort: "page",
  lbIndex: -1
};

export const isInline = img => img.url.startsWith("data:");
