"""Network access: every outgoing request goes through here."""
import base64
from collections import namedtuple
from urllib.parse import unquote, urljoin, urlparse

import requests

from .security import BlockedURL, assert_public

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
IMAGE_ACCEPT = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"

Page = namedtuple("Page", "url content content_type")


class Fetcher:
    def __init__(self, settings):
        self.settings = settings

    def get(self, url, headers=None, stream=False, max_redirects=5):
        """requests.get that validates every redirect hop when private IPs are blocked."""
        for _ in range(max_redirects + 1):
            if self.settings.block_private:
                assert_public(url)
            r = requests.get(
                url, headers=headers or HEADERS, timeout=self.settings.timeout,
                stream=stream, allow_redirects=False,
            )
            if r.is_redirect and r.headers.get("Location"):
                nxt = urljoin(url, r.headers["Location"])
                r.close()
                if urlparse(nxt).scheme not in ("http", "https"):
                    raise BlockedURL("unsupported redirect")
                url = nxt
                continue
            return r
        raise requests.exceptions.TooManyRedirects("too many redirects")

    @staticmethod
    def _read_limited(r, limit):
        chunks, size = [], 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > limit:
                raise ValueError("file too large")
            chunks.append(chunk)
        return b"".join(chunks)

    def fetch_page(self, url):
        r = self.get(url, stream=True)
        try:
            r.raise_for_status()
            content = self._read_limited(r, self.settings.max_page_bytes)
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
            return Page(r.url, content, ctype)
        finally:
            r.close()

    def fetch_image(self, url, ref=None):
        """Return (bytes, content_type) for an http(s) URL or a data: URI."""
        if url.startswith("data:"):
            header, _, payload = url.partition(",")
            mime = header[5:].split(";")[0]
            if ";base64" in header:
                return base64.b64decode(payload), mime
            return unquote(payload).encode(), mime

        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError("unsupported URL")
        headers = dict(HEADERS, Accept=IMAGE_ACCEPT)
        if ref:
            headers["Referer"] = ref  # helps with hotlink protection
        r = self.get(url, headers=headers, stream=True)
        try:
            r.raise_for_status()
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
            return self._read_limited(r, self.settings.max_image_bytes), ctype
        finally:
            r.close()
