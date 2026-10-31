"""File-name and extension helpers."""
import mimetypes
import os
import re
from urllib.parse import unquote, urlparse

KNOWN_EXTS = {"jpg", "png", "gif", "webp", "svg", "ico", "avif", "bmp"}


def ext_from_mime(mime):
    ext = (mimetypes.guess_extension(mime or "") or "").lower()
    return {".jpe": ".jpg", ".jpeg": ".jpg"}.get(ext, ext)


def _data_mime(url):
    return url[5:].split(";")[0].split(",")[0]


def ext_of(url):
    """Short, normalised extension used for the type filter chips."""
    if url.startswith("data:"):
        ext = ext_from_mime(_data_mime(url))
    else:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
    ext = ext.lstrip(".")
    if ext in ("jpeg", "jpe"):
        ext = "jpg"
    return ext if ext in KNOWN_EXTS else "other"


def filename_from_url(url, index):
    if url.startswith("data:"):
        ext = ext_from_mime(_data_mime(url)) or ".img"
        return "inline_{:03d}{}".format(index, ext)
    name = os.path.basename(unquote(urlparse(url).path)) or "image_{:03d}".format(index)
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)[:150]


def ensure_extension(name, content_type):
    if os.path.splitext(name)[1]:
        return name
    return name + (ext_from_mime(content_type) or ".img")


def unique_name(name, used):
    """Return a name not in `used` (case-insensitive) and remember it."""
    base, ext = os.path.splitext(name)
    candidate, n = name, 1
    while candidate.lower() in used:
        candidate = "{}_{}{}".format(base, n, ext)
        n += 1
    used.add(candidate.lower())
    return candidate
