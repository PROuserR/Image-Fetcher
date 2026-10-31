"""Runtime settings, read once from environment variables.

Local runs are permissive. When hosted (a PORT or HOSTED variable is set) the
safety limits switch on: private-address blocking, rate limits and size caps.
"""
import os
from dataclasses import dataclass, field

MB = 1024 * 1024


@dataclass(frozen=True)
class Settings:
    hosted: bool = False
    block_private: bool = False
    timeout: int = 15
    max_image_bytes: int = 30 * MB
    max_page_bytes: int = 8 * MB
    max_images: int = 500
    max_zip_images: int = 500
    max_zip_bytes: int = 1024 * MB
    zip_workers: int = 8
    rate_limits: dict = field(default_factory=dict)  # {"/api/scan": requests per minute, ...}

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        if env.get("PORT") or env.get("HOSTED"):
            return cls(
                hosted=True,
                block_private=True,
                max_image_bytes=10 * MB,
                max_zip_images=80,
                max_zip_bytes=80 * MB,
                rate_limits={"/api/scan": 20, "/api/zip": 8, "/api/proxy": 600},
            )
        return cls(block_private=env.get("BLOCK_PRIVATE") == "1")
