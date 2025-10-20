"""Lightweight HTTP helper that falls back to urllib when requests is unavailable."""
from __future__ import annotations

import json
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:  # pragma: no cover - optional dependency handling
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class HTTPErrorResponse(RuntimeError):
    """Raised when an HTTP request fails."""

    def __init__(self, status_code: int, message: str):
        # Builds a readable error message carrying the HTTP status code
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


def http_get(url: str, params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> Dict:
    # Prefers the requests library when it is available
    if requests:  # pragma: no cover - prefer requests when available
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if not response.ok:
            raise HTTPErrorResponse(response.status_code, response.text)
        return response.json()

    # Falls back to urllib with manual query string handling
    query_string = urlencode(params or {})
    full_url = f"{url}?{query_string}" if query_string else url
    request = Request(full_url, headers=headers or {})
    try:
        with urlopen(request, timeout=30) as response:  # nosec B310
            charset = response.headers.get_content_charset("utf-8")
            payload = response.read().decode(charset)
            return json.loads(payload)
    except HTTPError as exc:  # pragma: no cover - network failure path
        raise HTTPErrorResponse(exc.code, exc.reason) from exc
    except URLError as exc:  # pragma: no cover
        raise RuntimeError(f"Network error: {exc.reason}") from exc
