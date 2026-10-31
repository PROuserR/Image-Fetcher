"""SSRF protection and rate limiting."""
import ipaddress
import socket
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlparse


class BlockedURL(ValueError):
    """Raised when a URL points somewhere we refuse to fetch."""


def assert_public(url):
    """Refuse URLs that resolve to private, loopback or link-local addresses."""
    host = urlparse(url).hostname
    if not host:
        raise BlockedURL("invalid URL")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return  # unresolvable: the HTTP client will fail with a normal error
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global:
            raise BlockedURL("address not allowed")


class RateLimiter:
    """Tiny in-memory sliding-window limiter, keyed by (bucket, client)."""

    def __init__(self, limits, window=60):
        self.limits = dict(limits)
        self.window = window
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, bucket, client):
        limit = self.limits.get(bucket)
        if not limit:
            return True
        now = time.time()
        with self._lock:
            if len(self._hits) > 5000:  # keep memory bounded
                stale = [k for k, q in self._hits.items() if not q or q[-1] < now - self.window]
                for key in stale:
                    del self._hits[key]
            q = self._hits[(bucket, client)]
            while q and q[0] < now - self.window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
        return True
