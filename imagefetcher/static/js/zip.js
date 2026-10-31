import { $, h } from "./dom.js";
import { state } from "./state.js";
import { requestZip } from "./api.js";
import { toast } from "./toast.js";
import { updateBar } from "./selection.js";

export function initZip(button) {
  const spinner = $(".spinner", button);
  const label = $(".label", button);

  button.addEventListener("click", async () => {
    const urls = [...state.selected].sort((a, b) => a - b).map(i => state.images[i].url);
    if (!urls.length) return;

    button.disabled = true;
    spinner.hidden = false;
    label.textContent = "Preparing ZIP…";
    try {
      const { blob, failed } = await requestZip(urls, state.page);
      const link = h("a", { href: URL.createObjectURL(blob), download: `${state.host}-images.zip` });
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
      const saved = urls.length - failed;
      toast(failed ? `Saved ${saved} images (${failed} failed)` : `Saved ${saved} image${saved > 1 ? "s" : ""}`,
        failed ? "error" : "info");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      spinner.hidden = true;
      updateBar();
    }
  });
}
