# scripts/fetch/anilist.py
import time

import requests

from scripts.fetch.common import DEFAULT_USER_AGENT

ANILIST_API_URL = "https://graphql.anilist.co"

TRENDING_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(sort: TRENDING_DESC, type: ANIME) {
      title { romaji english }
      trending
      popularity
      siteUrl
    }
  }
}
"""


def parse_anilist_response(payload):
    data = payload.get("data") or {}
    page = data.get("Page") or {}
    media_list = page.get("media") or []
    entries = []
    for media in media_list:
        title_obj = media.get("title", {}) or {}
        title = title_obj.get("english") or title_obj.get("romaji") or ""
        if not title:
            continue
        entries.append(
            {
                "title": title,
                "trending_score": media.get("trending", 0),
                "popularity": media.get("popularity", 0),
                "site_url": media.get("siteUrl", ""),
            }
        )
    return entries


def fetch_trending_anime(per_page=25, timeout=15, max_retries=3, backoff_seconds=5):
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    payload = {"query": TRENDING_QUERY, "variables": {"page": 1, "perPage": per_page}}

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                ANILIST_API_URL,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return parse_anilist_response(response.json())
        except requests.RequestException as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(backoff_seconds)

    raise last_error
