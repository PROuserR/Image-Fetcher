"""Build a ZIP of many images with bounded memory use."""
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor

from .naming import ensure_extension, filename_from_url, unique_name


def build_zip(urls, fetch, max_bytes, workers=8, batch=8):
    """Download `urls` with `fetch(url) -> (bytes, content_type)`; return (BytesIO, failed_count)."""

    def job(item):
        index, url = item
        try:
            data, ctype = fetch(url)
            return index, url, data, ctype
        except Exception:  # noqa: BLE001 - one bad image must not sink the batch
            return index, url, None, ""

    buf, used = io.BytesIO(), set()
    failed = total = 0
    numbered = list(enumerate(urls, 1))
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf, ThreadPoolExecutor(max_workers=workers) as pool:
        for start in range(0, len(numbered), batch):  # small batches keep memory low
            for index, url, data, ctype in pool.map(job, numbered[start:start + batch]):
                if data is None or total + len(data) > max_bytes:
                    failed += 1
                    continue
                total += len(data)
                name = ensure_extension(filename_from_url(url, index), ctype)
                zf.writestr(unique_name(name, used), data)
    buf.seek(0)
    return buf, failed
