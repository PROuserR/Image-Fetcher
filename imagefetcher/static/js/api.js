// Everything that talks to the Flask backend.
import { state, isInline } from "./state.js";

async function post(path, payload) {
  try {
    return await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (_) {
    throw new Error("Can't reach the server. Is it still running?");
  }
}

const readJson = async res => { try { return await res.json(); } catch (_) { return {}; } };

export async function scanPage(url, extras) {
  const res = await post("/api/scan", { url, extras });
  const data = await readJson(res);
  if (!res.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

export async function requestZip(urls, ref) {
  const res = await post("/api/zip", { urls, ref });
  if (!res.ok) throw new Error((await readJson(res)).error || "Download failed.");
  return { blob: await res.blob(), failed: Number(res.headers.get("X-Failed") || 0) };
}

export const proxyUrl = img =>
  isInline(img)
    ? img.url
    : `/api/proxy?url=${encodeURIComponent(img.url)}&ref=${encodeURIComponent(state.page)}`;

export const downloadHref = img =>
  isInline(img) ? img.url : `${proxyUrl(img)}&download=1&name=${encodeURIComponent(img.name)}`;
