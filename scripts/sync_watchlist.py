# scripts/sync_watchlist.py
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_PATH = REPO_ROOT / "config" / "watchlist.yaml"
ANILIST_RAW_DIR = REPO_ROOT / "data" / "raw" / "anilist"
ANILIST_MANGA_RAW_DIR = REPO_ROOT / "data" / "raw" / "anilist-manga"


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


def build_aliases(entry):
    """Native and romaji titles usable as match aliases for this AniList entry.

    Drops blanks, duplicates, and any value equal to the canonical title
    (case-insensitively) — the canonical name is already matched on its own.
    """
    canonical = (entry.get("title") or "").strip()
    seen = {canonical.lower()}
    aliases = []
    for key in ("native_title", "romaji_title"):
        value = (entry.get(key) or "").strip()
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        aliases.append(value)
    return aliases


def find_new_entries(anilist_entries, watchlist_data):
    known = flatten_known_names(watchlist_data)
    new_entries = []
    seen_this_call = set()
    for entry in anilist_entries:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        key = title.lower()
        if key in known or key in seen_this_call:
            continue
        seen_this_call.add(key)
        new_entries.append(entry)
    return new_entries


def add_entries_to_watchlist(watchlist_data, new_entries, category):
    titles = list(watchlist_data.get("titles", []))
    for entry in new_entries:
        titles.append(
            {
                "canonical": (entry.get("title") or "").strip(),
                "category": category,
                "aliases": build_aliases(entry),
            }
        )
    return {"titles": titles}


def enrich_empty_aliases(watchlist_data, anilist_entries):
    """Fill in aliases for watchlist entries that have none.

    Matches on canonical name only (case-insensitively). Returns the updated
    data and whether anything actually changed, so callers can skip rewriting
    the file on a no-op run.
    """
    by_canonical = {}
    for entry in anilist_entries:
        title = (entry.get("title") or "").strip()
        if title:
            by_canonical.setdefault(title.lower(), entry)

    changed = False
    titles = []
    for item in watchlist_data.get("titles", []):
        if not item.get("aliases"):
            entry = by_canonical.get(item["canonical"].strip().lower())
            if entry:
                aliases = build_aliases(entry)
                if aliases:
                    item = {**item, "aliases": aliases}
                    changed = True
        titles.append(item)
    return {"titles": titles}, changed


def load_latest_anilist_entries(raw_dir=ANILIST_RAW_DIR):
    if not raw_dir.exists():
        return []
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        return []
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def run(
    anilist_raw_dir=ANILIST_RAW_DIR,
    anilist_manga_raw_dir=ANILIST_MANGA_RAW_DIR,
    watchlist_path=WATCHLIST_PATH,
):
    watchlist_data = load_watchlist_data(watchlist_path)
    anime_entries = load_latest_anilist_entries(anilist_raw_dir)
    manga_entries = load_latest_anilist_entries(anilist_manga_raw_dir)

    added = []
    # ANIME first so a title trending as both lands as anime, matching the
    # behaviour from before manga sync existed.
    for entries, category in ((anime_entries, "anime"), (manga_entries, "manga")):
        new_entries = find_new_entries(entries, watchlist_data)
        if new_entries:
            watchlist_data = add_entries_to_watchlist(watchlist_data, new_entries, category)
            added.extend((e.get("title") or "").strip() for e in new_entries)

    watchlist_data, enriched = enrich_empty_aliases(watchlist_data, anime_entries + manga_entries)

    if added or enriched:
        with open(watchlist_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(watchlist_data, f, allow_unicode=True, sort_keys=False)
    return added


if __name__ == "__main__":
    added = run()
    if added:
        print(f"Added {len(added)} new title(s) to watchlist: {added}")
