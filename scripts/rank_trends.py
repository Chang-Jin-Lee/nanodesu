import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_MENTIONS_DIR = REPO_ROOT / "data" / "mentions"
DATA_TRENDS_DIR = REPO_ROOT / "data" / "trends"

REGIONS = ("global", "japan")
CATEGORIES = ("anime", "manga", "game")
WINDOWS = (7, 30)


def load_mentions_in_window(mentions, reference_date, window_days):
    cutoff = reference_date - timedelta(days=window_days - 1)
    result = []
    for mention in mentions:
        date_str = mention.get("date")
        if not date_str:
            continue
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if cutoff <= parsed <= reference_date:
            result.append(mention)
    return result


def rank_mentions(mentions, region, category):
    """Count mentions per watch_title within a single region and category.

    Input is a list of mention records already filtered to one region+window
    (by the caller/window step). Records are first filtered to `region`, then
    deduplicated on (watch_title, item_url) so the same article captured
    across multiple fetch runs (or from multiple raw sources) only counts
    once per title. Records with a falsy item_url are never deduped against
    each other (an empty URL isn't a reliable dedup key) and always count.
    The `sources` set for each title still reflects every distinct source
    that ever mentioned it, even across the deduplicated mention count.

    Returns a list of {"title", "mentions", "sources"} dicts sorted by
    mentions descending, title ascending.
    """
    counts = defaultdict(int)
    sources = defaultdict(set)
    seen_urls = set()
    for mention in mentions:
        if mention.get("region") != region:
            continue
        if mention.get("category", "anime") != category:
            continue
        title = mention["watch_title"]
        sources[title].add(mention["source"])
        item_url = mention.get("item_url")
        if item_url:
            key = (title, item_url)
            if key in seen_urls:
                continue
            seen_urls.add(key)
        counts[title] += 1

    entries = [
        {"title": title, "mentions": count, "sources": sorted(sources[title])}
        for title, count in counts.items()
    ]
    entries.sort(key=lambda e: (-e["mentions"], e["title"]))
    return entries


def build_trend_report(all_mentions, region, category, window_days, reference_date):
    windowed = load_mentions_in_window(all_mentions, reference_date, window_days)
    entries = rank_mentions(windowed, region, category)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "region": region,
        "category": category,
        "window_days": window_days,
        "entries": entries,
    }


def load_previous_ranks(path):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {entry["title"]: idx + 1 for idx, entry in enumerate(data.get("entries", []))}


def attach_deltas(entries, previous_ranks):
    for idx, entry in enumerate(entries):
        current_rank = idx + 1
        previous_rank = previous_ranks.get(entry["title"])
        entry["delta"] = (previous_rank - current_rank) if previous_rank is not None else None
    return entries


def load_all_mentions(mentions_dir=DATA_MENTIONS_DIR):
    all_mentions = []
    if not mentions_dir.exists():
        return all_mentions
    for file_path in sorted(mentions_dir.glob("*.json")):
        with open(file_path, encoding="utf-8") as f:
            all_mentions.extend(json.load(f))
    return all_mentions


def run(reference_date=None, mentions_dir=DATA_MENTIONS_DIR, out_dir=DATA_TRENDS_DIR):
    reference_date = reference_date or datetime.now(timezone.utc).date()
    all_mentions = load_all_mentions(mentions_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for region in REGIONS:
        for category in CATEGORIES:
            for window_days in WINDOWS:
                out_path = out_dir / f"{region}-{category}-{window_days}d.json"
                previous_ranks = load_previous_ranks(out_path)
                report = build_trend_report(all_mentions, region, category, window_days, reference_date)
                report["entries"] = attach_deltas(report["entries"], previous_ranks)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
