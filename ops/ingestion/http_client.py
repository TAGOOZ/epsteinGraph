import urllib.request
from typing import Any


def fetch_url(
    url: str,
    *,
    user_agent: str,
    extra_headers: dict[str, str] | None = None,
) -> tuple[bytes, str] | tuple[bytes, str, dict[str, str], int] | None:
    headers = {"User-Agent": user_agent}
    if extra_headers:
        headers.update(extra_headers)

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            final_url = response.geturl()
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            return content, final_url, response_headers, response.status
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return b"", url, {k.lower(): v for k, v in exc.headers.items()}, 304
        return None
    except Exception:
        return None
