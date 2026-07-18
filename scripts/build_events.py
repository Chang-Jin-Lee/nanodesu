# scripts/build_events.py
import json
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_EVENTS_RAW_DIR = REPO_ROOT / "data" / "events" / "collabocafe"
CONVENTIONS_PATH = REPO_ROOT / "config" / "conventions.yaml"
EVENTS_OUT_PATH = REPO_ROOT / "data" / "events" / "japan-events.json"


def load_latest_collabocafe_events(raw_dir=DATA_EVENTS_RAW_DIR):
    if not raw_dir.exists():
        return []
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        return []
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def load_conventions(path=CONVENTIONS_PATH):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    events = []
    for entry in data.get("conventions", []):
        events.append(
            {
                "title": entry["title"],
                "venue": entry.get("venue", ""),
                "start_date": entry.get("start_date"),
                "end_date": entry.get("end_date"),
                "url": entry.get("url", ""),
                "source_site": "conventions.yaml",
            }
        )
    return events


def dedupe_events(events):
    seen = set()
    result = []
    for event in events:
        key = (event["title"], event.get("venue", ""), event.get("start_date"))
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def drop_past_events(events, today):
    kept = []
    for event in events:
        end_date = event.get("end_date")
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                if end < today:
                    continue
            except ValueError:
                pass
        kept.append(event)
    return kept


def sort_events(events):
    def sort_key(event):
        return event.get("start_date") or "9999-99-99"

    return sorted(events, key=sort_key)


def build_events(collabocafe_events, convention_events, today):
    combined = collabocafe_events + convention_events
    combined = dedupe_events(combined)
    combined = drop_past_events(combined, today)
    return sort_events(combined)


def run(today=None, raw_dir=DATA_EVENTS_RAW_DIR, conventions_path=CONVENTIONS_PATH, out_path=EVENTS_OUT_PATH):
    today = today or datetime.now(timezone.utc).date()
    collabocafe_events = load_latest_collabocafe_events(raw_dir=raw_dir)
    convention_events = load_conventions(path=conventions_path)
    events = build_events(collabocafe_events, convention_events, today)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    return events


if __name__ == "__main__":
    run()
