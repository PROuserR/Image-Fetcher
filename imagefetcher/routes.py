"""HTTP endpoints."""
import mimetypes
import re
from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_file

from .archive import build_zip
from .naming import ext_of, filename_from_url
from .scraper import parse_page
from .security import BlockedURL

bp = Blueprint("main", __name__)


def _svc():
    return current_app.extensions["imagefetcher"]


def _error(message, status):
    return jsonify(error=message), status


def _describe_fetch_error(exc):
    """Map a fetching exception to (friendly message, HTTP status)."""
    if isinstance(exc, BlockedURL):
        return "That address can't be fetched.", 400
    if isinstance(exc, (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL,
                        requests.exceptions.InvalidSchema)):
        return "That doesn't look like a valid URL.", 400
    if isinstance(exc, requests.exceptions.Timeout):
        return "The site took too long to respond.", 504
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "Couldn't connect. Check the address and your internet connection.", 502
    if isinstance(exc, requests.exceptions.HTTPError):
        code = exc.response.status_code if exc.response is not None else "?"
        return "The site returned an error (HTTP {}).".format(code), 502
    if isinstance(exc, requests.RequestException):
        return "Request failed: {}".format(exc), 502
    return "That page is too large to scan.", 400  # ValueError from the size cap


@bp.before_request
def throttle():
    if not _svc().limiter.allow(request.path, request.remote_addr):
        return _error("Too many requests - please wait a minute and try again.", 429)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/healthz")
def healthz():
    return "ok"


@bp.post("/api/scan")
def scan():
    svc = _svc()
    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    extras = bool(body.get("extras", True))
    if not url:
        return _error("Please enter a URL.", 400)
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url

    try:
        page = svc.fetcher.fetch_page(url)
    except (requests.RequestException, ValueError) as exc:
        return _error(*_describe_fetch_error(exc))

    if page.content_type.startswith("image/"):
        title, urls = "", [page.url]  # the link itself is an image
    else:
        title, urls = parse_page(page.content, page.url, extras)

    cap = svc.settings.max_images
    truncated = len(urls) > cap
    images = [
        {"url": u, "name": filename_from_url(u, i + 1), "ext": ext_of(u)}
        for i, u in enumerate(urls[:cap])
    ]
    return jsonify(page=page.url, title=title, images=images, truncated=truncated)


@bp.get("/api/proxy")
def proxy():
    """Serve an image through this server so thumbnails work despite hotlink rules."""
    url = request.args.get("url", "")
    ref = request.args.get("ref") or None
    if urlparse(url).scheme not in ("http", "https"):
        return _error("Bad URL", 400)
    try:
        data, ctype = _svc().fetcher.fetch_image(url, ref)
    except Exception as exc:  # noqa: BLE001
        return _error(str(exc), 502)

    name = filename_from_url(url, 1)
    if not (ctype.startswith("image/") or ctype in ("", "application/octet-stream", "binary/octet-stream")):
        return _error("Not an image", 415)
    if not ctype.startswith("image/"):
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"

    resp = Response(data, mimetype=ctype)
    resp.headers["Cache-Control"] = "private, max-age=600"
    # Stops SVGs from running scripts if opened directly in a tab.
    resp.headers["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'unsafe-inline'"
    if request.args.get("download"):
        fname = re.sub(r"[^\w.\- ]", "_", request.args.get("name") or name)
        resp.headers["Content-Disposition"] = 'attachment; filename="{}"'.format(fname)
    return resp


@bp.post("/api/zip")
def zip_images():
    svc = _svc()
    body = request.get_json(silent=True) or {}
    urls = [u for u in (body.get("urls") or []) if isinstance(u, str)]
    ref = body.get("ref") or None
    if not urls:
        return _error("No images selected.", 400)
    if len(urls) > svc.settings.max_zip_images:
        return _error("Please select at most {} images at a time.".format(svc.settings.max_zip_images), 400)

    buf, failed = build_zip(
        urls,
        fetch=lambda u: svc.fetcher.fetch_image(u, ref),  # no current_app inside worker threads
        max_bytes=svc.settings.max_zip_bytes,
        workers=svc.settings.zip_workers,
    )
    if failed == len(urls):
        return _error("None of the selected images could be downloaded.", 502)

    resp = send_file(buf, mimetype="application/zip", as_attachment=True, download_name="images.zip")
    resp.headers["X-Failed"] = str(failed)
    resp.headers["Access-Control-Expose-Headers"] = "X-Failed"
    return resp
