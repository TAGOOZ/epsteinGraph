import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from http_client import fetch_url
from rate_limiter import RateLimiter


def download_all(
    *,
    urls: list[str],
    state: dict,
    download_dir: Path,
    rate_limit_seconds: float,
    user_agent: str,
) -> dict:
    limiter = RateLimiter(rate_limit_seconds)

    url_meta = state.setdefault("url_meta", {})
    file_index = state.setdefault("files", {})

    for url in urls:
        cached = url_meta.get(url)
        headers = {}
        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]

        limiter.wait()
        result = fetch_url(url, user_agent=user_agent, extra_headers=headers)
        if result is None:
            continue
        content, final_url, response_headers, status = result

        if status == 304 and cached:
            continue

        sha256 = hashlib.sha256(content).hexdigest()
        file_path = download_dir / sha256
        if not file_path.exists():
            file_path.write_bytes(content)

        url_meta[url] = {
            "final_url": final_url,
            "etag": response_headers.get("etag"),
            "last_modified": response_headers.get("last-modified"),
            "sha256": sha256,
            "path": str(file_path),
            "source_host": urlparse(final_url).netloc,
        }
        file_index.setdefault(sha256, {"path": str(file_path)})

    return state
