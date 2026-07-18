# scripts/sync_watchlist.py
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = REPO_ROOT / "config" / "watchlist.yaml"
ANILIST_RAW_DIR = REPO_ROOT / "data" / "raw" / "anilist"


def load_watchlist_data(path=WATCHLIST_PATH):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {"titles": []}


def flatten_known_names(watchlist_data):
    known = set()
    for entry in watchlist_data.get("titles", []):
        known.add(entry["canonical"].strip().lower())
        for alias in entry.get("aliases", []):
            known.add(alias.strip().lower())
    return known


def find_new_titles(anilist_entries, watchlist_data):
    known = flatten_known_names(watchlist_data)
    new_titles = []
    seen_this_call = set()
    for entry in anilist_entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        key = title.lower()
        if key in known or key in seen_this_call:
            continue
        seen_this_call.add(key)
        new_titles.append(title)
    return new_titles


def add_titles_to_watchlist(watchlist_data, new_titles):
    titles = list(watchlist_data.get("titles", []))
    for title in new_titles:
        titles.append({"canonical": title, "category": "anime", "aliases": []})
    return {"titles": titles}


def load_latest_anilist_entries(raw_dir=ANILIST_RAW_DIR):
    if not raw_dir.exists():
        return []
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        return []
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def run(anilist_raw_dir=ANILIST_RAW_DIR, watchlist_path=WATCHLIST_PATH):
    watchlist_data = load_watchlist_data(watchlist_path)
    anilist_entries = load_latest_anilist_entries(anilist_raw_dir)
    new_titles = find_new_titles(anilist_entries, watchlist_data)
    if new_titles:
        updated = add_titles_to_watchlist(watchlist_data, new_titles)
        with open(watchlist_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(updated, f, allow_unicode=True, sort_keys=False)
    return new_titles


if __name__ == "__main__":
    added = run()
    if added:
        print(f"Added {len(added)} new title(s) to watchlist: {added}")
