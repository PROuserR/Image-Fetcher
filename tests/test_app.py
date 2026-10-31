"""Offline tests: run with  python -m unittest discover -s tests -v"""
import base64
import io
import os
import sys
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup  # noqa: E402

from imagefetcher import create_app  # noqa: E402
from imagefetcher.config import Settings  # noqa: E402
from imagefetcher.fetcher import Fetcher  # noqa: E402
from imagefetcher.naming import ensure_extension, ext_of, filename_from_url, unique_name  # noqa: E402
from imagefetcher.scraper import best_from_srcset, extract_image_urls, parse_page  # noqa: E402
from imagefetcher.security import BlockedURL, RateLimiter, assert_public  # noqa: E402

PNG = "data:image/png;base64," + base64.b64encode(b"fake-png").decode()
HOSTED = Settings.from_env({"HOSTED": "1"})


class ScraperTests(unittest.TestCase):
    def test_srcset_picks_largest(self):
        self.assertEqual(best_from_srcset("a.jpg 1x, b.jpg 2x, c.jpg 1.5x"), "b.jpg")
        self.assertEqual(best_from_srcset("s.jpg 400w, l.jpg 1200w"), "l.jpg")

    def test_extract_all_sources(self):
        html = (
            '<meta property="og:image" content="/og.jpg"><link rel="icon" href="/fav.ico">'
            '<img src="a.png" srcset="b-1x.jpg 1x, b-2x.jpg 2x"><img data-src="lazy.webp">'
            "<div style=\"background:url('/bg.png')\"></div><img src=\"{}\"><img src=\"javascript:x\">".format(PNG)
        )
        urls = extract_image_urls(BeautifulSoup(html, "html.parser"), "https://x.com/p/")
        self.assertEqual(urls, [
            "https://x.com/p/a.png", "https://x.com/p/b-2x.jpg", "https://x.com/p/lazy.webp", PNG,
            "https://x.com/og.jpg", "https://x.com/fav.ico", "https://x.com/bg.png",
        ])

    def test_extras_can_be_disabled(self):
        html = '<meta property="og:image" content="/og.jpg"><img src="a.png">'
        self.assertEqual(parse_page(html, "https://x.com/", include_extras=False).urls, ["https://x.com/a.png"])

    def test_title(self):
        self.assertEqual(parse_page("<title> Hi </title>", "https://x.com/").title, "Hi")


class NamingTests(unittest.TestCase):
    def test_ext_and_names(self):
        self.assertEqual(ext_of("https://x.com/a.JPEG"), "jpg")
        self.assertEqual(ext_of("https://x.com/a.xyz"), "other")
        self.assertEqual(ext_of(PNG), "png")
        self.assertEqual(filename_from_url("https://x.com/dir/pic%20one.png?x=1", 1), "pic one.png")
        self.assertEqual(filename_from_url("https://x.com/", 7), "image_007")
        self.assertEqual(ensure_extension("img", "image/png"), "img.png")

    def test_unique_name(self):
        used = set()
        self.assertEqual([unique_name("a.png", used) for _ in range(3)], ["a.png", "a_1.png", "a_2.png"])


class SecurityTests(unittest.TestCase):
    def test_blocks_private_targets(self):
        for url in ("http://127.0.0.1/", "http://localhost/", "http://169.254.169.254/",
                    "http://10.0.0.5/", "http://[::ffff:127.0.0.1]/", "http://[::1]/"):
            with self.assertRaises(BlockedURL, msg=url):
                assert_public(url)

    def test_allows_public_ip(self):
        assert_public("http://93.184.216.34/")

    def test_redirect_to_private_is_blocked(self):
        class Redirect:
            is_redirect = True
            headers = {"Location": "http://127.0.0.1/admin"}
            def close(self): pass

        with mock.patch("imagefetcher.fetcher.requests.get", return_value=Redirect()):
            with self.assertRaises(BlockedURL):
                Fetcher(HOSTED).get("http://93.184.216.34/")

    def test_rate_limiter(self):
        rl = RateLimiter({"/x": 2})
        self.assertEqual([rl.allow("/x", "ip") for _ in range(3)], [True, True, False])
        self.assertTrue(rl.allow("/x", "other-ip"))
        self.assertTrue(rl.allow("/unlimited", "ip"))


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(Settings()).test_client()

    def test_pages_and_static_assets(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/healthz").data, b"ok")
        js = self.client.get("/static/js/main.js")
        self.assertEqual(js.status_code, 200)
        self.assertIn("javascript", js.headers["Content-Type"])  # ES modules need a JS MIME type
        self.assertIn("text/css", self.client.get("/static/css/components.css").headers["Content-Type"])

    def test_security_headers(self):
        r = self.client.get("/")
        self.assertIn("script-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")

    def test_scan_validation(self):
        self.assertEqual(self.client.post("/api/scan", json={}).status_code, 400)

    def test_scan_success(self):
        from imagefetcher.fetcher import Page
        html = b"<title>T</title><img src='/a.png'><img src='/b.jpg'>"
        with mock.patch.object(Fetcher, "fetch_page", return_value=Page("https://x.com/", html, "text/html")):
            data = self.client.post("/api/scan", json={"url": "x.com"}).get_json()
        self.assertEqual(data["title"], "T")
        self.assertEqual([i["name"] for i in data["images"]], ["a.png", "b.jpg"])

    def test_scan_direct_image_link(self):
        from imagefetcher.fetcher import Page
        with mock.patch.object(Fetcher, "fetch_page", return_value=Page("https://x.com/p.png", b"", "image/png")):
            data = self.client.post("/api/scan", json={"url": "https://x.com/p.png"}).get_json()
        self.assertEqual([i["url"] for i in data["images"]], ["https://x.com/p.png"])

    def test_scan_connection_error(self):
        import requests
        with mock.patch.object(Fetcher, "fetch_page", side_effect=requests.exceptions.ConnectionError()):
            r = self.client.post("/api/scan", json={"url": "https://nope.invalid"})
        self.assertEqual(r.status_code, 502)

    def test_proxy_rejects_bad_scheme(self):
        self.assertEqual(self.client.get("/api/proxy?url=file:///etc/passwd").status_code, 400)

    def test_proxy_serves_image_with_sandbox_csp(self):
        with mock.patch.object(Fetcher, "fetch_image", return_value=(b"x", "image/svg+xml")):
            r = self.client.get("/api/proxy?url=https://x.com/a.svg&download=1&name=a.svg")
        self.assertEqual(r.status_code, 200)
        self.assertIn("sandbox", r.headers["Content-Security-Policy"])
        self.assertIn("attachment", r.headers["Content-Disposition"])

    def test_zip(self):
        r = self.client.post("/api/zip", json={"urls": [PNG, PNG]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["X-Failed"], "0")
        self.assertEqual(zipfile.ZipFile(io.BytesIO(r.data)).namelist(), ["inline_001.png", "inline_002.png"])

    def test_zip_partial_failure(self):
        r = self.client.post("/api/zip", json={"urls": [PNG, "ftp://bad"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["X-Failed"], "1")

    def test_zip_all_fail_and_empty(self):
        self.assertEqual(self.client.post("/api/zip", json={"urls": ["ftp://bad"]}).status_code, 502)
        self.assertEqual(self.client.post("/api/zip", json={"urls": []}).status_code, 400)


class HostedTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(HOSTED).test_client()

    def test_private_scan_blocked(self):
        r = self.client.post("/api/scan", json={"url": "http://169.254.169.254/latest/meta-data/"})
        self.assertEqual(r.status_code, 400)

    def test_zip_cap(self):
        self.assertEqual(self.client.post("/api/zip", json={"urls": [PNG] * 81}).status_code, 400)

    def test_rate_limit(self):
        codes = [self.client.post("/api/scan", json={}).status_code for _ in range(22)]
        self.assertEqual(codes[0], 400)
        self.assertEqual(codes[-1], 429)


if __name__ == "__main__":
    unittest.main()
