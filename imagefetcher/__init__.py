"""Image Fetcher - find and download every image on a webpage."""
import mimetypes
from types import SimpleNamespace

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Settings
from .fetcher import Fetcher
from .routes import bp
from .security import RateLimiter

PAGE_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
)


def create_app(settings=None):
    settings = settings or Settings.from_env()

    # Windows registries sometimes map .js to text/plain, which breaks ES modules.
    mimetypes.add_type("text/javascript", ".js")
    mimetypes.add_type("text/css", ".css")

    app = Flask(__name__)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600 if settings.hosted else 0
    if settings.hosted:
        # Trust the platform's reverse proxy so request.remote_addr is the real client.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.extensions["imagefetcher"] = SimpleNamespace(
        settings=settings,
        fetcher=Fetcher(settings),
        limiter=RateLimiter(settings.rate_limits),
    )
    app.register_blueprint(bp)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("Content-Security-Policy", PAGE_CSP)
        return resp

    return app
