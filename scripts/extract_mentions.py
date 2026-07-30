# scripts/extract_mentions.py
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

_ASCII_NAME_RE = re.compile(r"^[A-Za-z0-9 .:'!\-]+$")

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = REPO_ROOT / "config" / "watchlist.yaml"
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
DATA_MENTIONS_DIR = REPO_ROOT / "data" / "mentions"


def load_watchlist(path=WATCHLIST_PATH):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entries = []
    for entry in data.get("titles", []):
        canonical = entry["canonical"]
        names = [canonical] + entry.get("aliases", [])
        category = entry.get("category", "anime")
        entries.append((canonical, names, category))
    return entries


def find_mentions(item_title, watchlist):
    matches = []
    lowered = item_title.lower()
    for canonical, names, _category in watchlist:
        for name in names:
            if not name:
                continue
            is_ascii_name = bool(_ASCII_NAME_RE.match(name)) and any(c.isalnum() for c in name)
            if is_ascii_name:
                pattern = r"(?<![A-Za-z0-9])" + re.escape(name.lower()) + r"(?![A-Za-z0-9])"
                if re.search(pattern, lowered):
                    matches.append(canonical)
                    break
            else:
                if name.lower() in lowered:
                    matches.append(canonical)
                    break
    return matches


def extract_mentions_from_items(items, watchlist):
    categories = {canonical: category for canonical, _names, category in watchlist}
    mentions = []
    for item in items:
        title = item.get("title", "")
        for canonical in find_mentions(title, watchlist):
            mentions.append(
                {
                    "watch_title": canonical,
                    "category": item.get("category") or categories[canonical],
                    "region": item.get("region", ""),
                    "date": item.get("published", ""),
                    "source": item.get("source", ""),
                    "item_url": item.get("url", ""),
                }
            )
    return mentions


def collect_items_for_date(date_str, raw_dir=DATA_RAW_DIR):
    items = []
    if not raw_dir.exists():
        return items
    for source_dir in sorted(raw_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        if source_dir.name.startswith("anilist"):
            # AniList raw items (both `anilist` and `anilist-manga`) have a
            # different shape ({"title", "native_title", "romaji_title",
            # "trending_score", "popularity", "site_url"}) with no region,
            # published date, or url field, so they don't belong in the
            # mention-scanning pipeline.
            continue
        file_path = source_dir / f"{date_str}.json"
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                items.extend(json.load(f))
    return items


def run(date_str, watchlist_path=WATCHLIST_PATH, raw_dir=DATA_RAW_DIR, mentions_dir=DATA_MENTIONS_DIR):
    watchlist = load_watchlist(watchlist_path)
    items = collect_items_for_date(date_str, raw_dir=raw_dir)
    mentions = extract_mentions_from_items(items, watchlist)
    mentions_dir.mkdir(parents=True, exist_ok=True)
    with open(mentions_dir / f"{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(mentions, f, ensure_ascii=False, indent=2)
    return mentions


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run(date_arg)
