export const typeLabel = img => (img.ext === "other" ? "image" : img.ext.toUpperCase());
export const metaLabel = img => (img.w ? `${typeLabel(img)} · ${img.w} × ${img.h}` : typeLabel(img));
