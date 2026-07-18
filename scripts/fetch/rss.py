from datetime import datetime, timezone

import feedparser

from scripts.fetch.common import fetch_url


def parse_feed_text(text, source, region):
    parsed = feedparser.parse(text)
    items = []
    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            continue

        published = ""
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            published = datetime(*time_struct[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")

        items.append(
            {
                "title": title,
                "url": link,
                "published": published,
                "source": source,
                "region": region,
                "summary": entry.get("summary", "").strip(),
            }
        )
    return items


def fetch_rss(url, source, region, extra_headers=None):
    text = fetch_url(url, headers=extra_headers)
    return parse_feed_text(text, source, region)
