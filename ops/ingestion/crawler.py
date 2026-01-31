import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from http_client import fetch_url
from rate_limiter import RateLimiter


class LinkExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = None
        for key, value in attrs:
            if key == "href":
                href = value
                break
        if not href:
            return
        self.links.add(urljoin(self.base_url, href))


def crawl_listing_pages(
    *,
    seeds: list[str],
    allowed_hosts: set[str],
    blocked_path_substrings: set[str],
    allowed_extensions: set[str],
    rate_limit_seconds: float,
    user_agent: str,
) -> set[str]:
    limiter = RateLimiter(rate_limit_seconds)
    found: set[str] = set()

    for seed in seeds:
        limiter.wait()
        html_bytes, final_url = fetch_url(seed, user_agent=user_agent)
        extractor = LinkExtractor(final_url)
        extractor.feed(html_bytes.decode("utf-8", errors="ignore"))
        links = filter_links(
            extractor.links,
            allowed_hosts=allowed_hosts,
            blocked_path_substrings=blocked_path_substrings,
            allowed_extensions=allowed_extensions,
        )
        found.update(links)
        time.sleep(0.01)

    return found


def filter_links(
    links: set[str],
    *,
    allowed_hosts: set[str],
    blocked_path_substrings: set[str],
    allowed_extensions: set[str],
) -> set[str]:
    filtered: set[str] = set()

    for link in links:
        parsed = urlparse(link)
        if parsed.scheme not in {"http", "https"}:
            continue
        host = parsed.netloc.lower()
        if host not in allowed_hosts:
            continue
        if any(blocked in parsed.path for blocked in blocked_path_substrings):
            continue
        if allowed_extensions:
            path_lower = parsed.path.lower()
            if not any(path_lower.endswith(ext) for ext in allowed_extensions):
                continue
        filtered.add(link)

    return filtered
