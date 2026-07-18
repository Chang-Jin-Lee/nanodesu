import time

import requests

DEFAULT_USER_AGENT = (
    "nanodesu-tracker/1.0 (+https://github.com/nanodesu; "
    "subculture trend digest, contact via repo issues)"
)


class FetchError(Exception):
    """Raised when a URL could not be fetched after all retries."""


def fetch_url(url, headers=None, timeout=15, max_retries=3, backoff_seconds=5):
    merged_headers = dict(headers) if headers else {}
    merged_headers["User-Agent"] = DEFAULT_USER_AGENT

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=merged_headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(backoff_seconds)

    raise FetchError(f"failed to fetch {url} after {max_retries} attempts: {last_error}")
