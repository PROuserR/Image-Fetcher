"""HTML parsing: find every image URL on a page."""
import re
from collections import namedtuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

LAZY_ATTRS = ("src", "data-src", "data-original", "data-lazy-src")
SRCSET_ATTRS = ("srcset", "data-srcset")
SOCIAL_KEYS = {"og:image", "twitter:image", "og:image:url"}
CSS_URL = re.compile(r"url\((['\"]?)(.*?)\1\)")

ParsedPage = namedtuple("ParsedPage", "title urls")


def best_from_srcset(srcset):
    """Return the highest-resolution URL from a srcset attribute."""
    best_url, best_score = None, -1.0
    for candidate in re.split(r",\s+", srcset.strip()):
        parts = candidate.strip().split()
        if not parts:
            continue
        score = 1.0
        if len(parts) > 1:
            try:
                score = float(parts[1].rstrip("wxWX"))
            except ValueError:
                pass
        if score > best_score:
            best_url, best_score = parts[0], score
    return best_url


def extract_image_urls(soup, base_url, include_extras=True):
    """Ordered, de-duplicated list of absolute image URLs."""
    found, seen = [], set()

    def add(raw):
        raw = (raw or "").strip()
        if not raw:
            return
        if raw.startswith("data:image"):
            full = raw
        else:
            full = urljoin(base_url, raw)
            if urlparse(full).scheme not in ("http", "https"):
                return
        if full not in seen:
            seen.add(full)
            found.append(full)

    for img in soup.find_all("img"):
        for attr in LAZY_ATTRS:
            add(img.get(attr))
        for attr in SRCSET_ATTRS:
            if img.get(attr):
                add(best_from_srcset(img[attr]))

    for source in soup.find_all("source"):
        for attr in SRCSET_ATTRS:
            if source.get(attr):
                add(best_from_srcset(source[attr]))

    if include_extras:
        for meta in soup.find_all("meta"):
            key = (meta.get("property") or meta.get("name") or "").lower()
            if key in SOCIAL_KEYS:
                add(meta.get("content"))
        for link in soup.find_all("link"):
            if "icon" in " ".join(link.get("rel") or []).lower():
                add(link.get("href"))
        for tag in soup.find_all(style=True):
            for match in CSS_URL.findall(tag["style"]):
                add(match[1])

    return found


def parse_page(content, base_url, include_extras=True):
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    return ParsedPage(title, extract_image_urls(soup, base_url, include_extras))
