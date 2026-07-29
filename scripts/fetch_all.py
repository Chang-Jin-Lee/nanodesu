# scripts/fetch_all.py
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.fetch.rss import fetch_rss
from scripts.fetch.anilist import fetch_trending_anime
from scripts.fetch.steam_news import fetch_steam_news
from scripts.fetch.scrape_magazines import fetch_all_magazines
from scripts.fetch.scrape_collabocafe import fetch_collabocafe_events

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "sources.yaml"
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
DATA_EVENTS_DIR = REPO_ROOT / "data" / "events"
STATUS_PATH = REPO_ROOT / "data" / "status.json"


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def run(config=None, date_str=None):
    config = config or load_config()
    date_str = date_str or today_str()
    status = {}

    for source in config.get("sources", []):
        slug = source["slug"]
        try:
            items = fetch_rss(
                source["url"],
                source=slug,
                region=source["region"],
                category=source.get("category"),
            )
            write_json(DATA_RAW_DIR / slug / f"{date_str}.json", items)
            status[slug] = {"ok": True, "count": len(items)}
        except Exception as exc:
            status[slug] = {"ok": False, "error": str(exc), "optional": source.get("optional", False)}
        if source.get("crawl_delay"):
            time.sleep(source["crawl_delay"])

    if config.get("anilist", {}).get("enabled"):
        try:
            entries = fetch_trending_anime()
            write_json(DATA_RAW_DIR / "anilist" / f"{date_str}.json", entries)
            status["anilist"] = {"ok": True, "count": len(entries)}
        except Exception as exc:
            status["anilist"] = {"ok": False, "error": str(exc)}

    for steam_title in config.get("steam_titles", []):
        slug = f"steam-{steam_title['appid']}"
        try:
            items = fetch_steam_news(steam_title["appid"], steam_title["title"])
            write_json(DATA_RAW_DIR / slug / f"{date_str}.json", items)
            status[slug] = {"ok": True, "count": len(items)}
        except Exception as exc:
            status[slug] = {"ok": False, "error": str(exc)}

    if config.get("magazines", {}).get("enabled"):
        try:
            items = fetch_all_magazines()
            write_json(DATA_RAW_DIR / "magazines" / f"{date_str}.json", items)
            status["magazines"] = {"ok": True, "count": len(items)}
        except Exception as exc:
            status["magazines"] = {"ok": False, "error": str(exc)}

    if config.get("events", {}).get("collabocafe", {}).get("enabled"):
        try:
            events = fetch_collabocafe_events()
            write_json(DATA_EVENTS_DIR / "collabocafe" / f"{date_str}.json", events)
            status["collabocafe"] = {"ok": True, "count": len(events)}
        except Exception as exc:
            status["collabocafe"] = {"ok": False, "error": str(exc)}

    write_json(STATUS_PATH, {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": status})
    return status


if __name__ == "__main__":
    result = run()
    failed = [slug for slug, s in result.items() if not s.get("ok") and not s.get("optional")]
    if failed:
        print(f"warning: {len(failed)} required source(s) failed: {failed}", file=sys.stderr)
    sys.exit(0)
