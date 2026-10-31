import { isInline } from "./state.js";
import { toast } from "./toast.js";

export async function copyUrl(img) {
  if (isInline(img)) { toast("Inline images have no URL to copy.", "error"); return; }
  try {
    await navigator.clipboard.writeText(img.url);
    toast("URL copied to clipboard");
  } catch (_) {
    toast("Couldn't access the clipboard.", "error");
  }
}
