import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_TRENDS_DIR = REPO_ROOT / "data" / "trends"
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
DATA_EVENTS_PATH = REPO_ROOT / "data" / "events" / "japan-events.json"
REPORTS_DIR = REPO_ROOT / "reports"
README_PATH = REPO_ROOT / "README.md"


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def format_delta(delta):
    if delta is None:
        return "NEW"
    if delta > 0:
        return f"▲{delta}"
    if delta < 0:
        return f"▼{abs(delta)}"
    return "-"


CATEGORIES = (("anime", "Anime"), ("manga", "Manga"), ("game", "Game"))


def render_buzz_sections(region):
    content = ""
    for window in (7, 30):
        for category, label in CATEGORIES:
            trend = load_json(
                DATA_TRENDS_DIR / f"{region}-{category}-{window}d.json", default={"entries": []}
            )
            content += f"## {label} Buzz — Last {window} Days\n\n" + render_trend_table(trend["entries"]) + "\n"
    return content


def render_trend_table(entries, limit=None):
    rows = entries if limit is None else entries[:limit]
    if not rows:
        return "_No data yet._\n"
    lines = ["| # | Title | Mentions | Δ | Sources |", "|---|---|---|---|---|"]
    for i, entry in enumerate(rows, start=1):
        sources = ", ".join(entry["sources"])
        delta_str = format_delta(entry.get("delta"))
        lines.append(f"| {i} | {entry['title']} | {entry['mentions']} | {delta_str} | {sources} |")
    return "\n".join(lines) + "\n"


def render_anilist_table(entries, limit=10):
    rows = entries[:limit]
    if not rows:
        return "_No data yet._\n"
    lines = ["| # | Title | Trending | Popularity |", "|---|---|---|---|"]
    for i, entry in enumerate(rows, start=1):
        lines.append(
            f"| {i} | [{entry['title']}]({entry['site_url']}) | {entry['trending_score']} | {entry['popularity']} |"
        )
    return "\n".join(lines) + "\n"


def render_events_table(events):
    if not events:
        return "_No upcoming events._\n"
    lines = ["| Title | Venue | Start | End | Source |", "|---|---|---|---|---|"]
    for event in events:
        link = event.get("url") or event.get("source_url", "")
        lines.append(
            f"| {event['title']} | {event.get('venue', '')} | {event.get('start_date') or '-'} | "
            f"{event.get('end_date') or '-'} | [link]({link}) |"
        )
    return "\n".join(lines) + "\n"


def replace_marker_section(readme_text, name, new_body):
    pattern = re.compile(
        r"<!--START_SECTION:" + re.escape(name) + r"-->.*?<!--END_SECTION:" + re.escape(name) + r"-->",
        re.DOTALL,
    )
    replacement = f"<!--START_SECTION:{name}-->\n{new_body}\n<!--END_SECTION:{name}-->"
    if pattern.search(readme_text):
        return pattern.sub(replacement, readme_text)
    return readme_text + "\n\n" + replacement + "\n"


def latest_anilist_entries(subdir="anilist"):
    anilist_dir = DATA_RAW_DIR / subdir
    if not anilist_dir.exists():
        return []
    files = sorted(anilist_dir.glob("*.json"))
    if not files:
        return []
    return load_json(files[-1], default=[])


def render_global_report():
    anime_entries = latest_anilist_entries("anilist")
    manga_entries = latest_anilist_entries("anilist-manga")

    content = "# Global Trend Report\n\n"
    content += "## AniList Trending Anime\n\n" + render_anilist_table(anime_entries) + "\n"
    content += "## AniList Trending Manga\n\n" + render_anilist_table(manga_entries) + "\n"
    content += render_buzz_sections("global")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "global.md").write_text(content, encoding="utf-8")
    return content


def render_japan_report():
    events = load_json(DATA_EVENTS_PATH, default=[])

    content = "# Japan Trend Report\n\n"
    content += render_buzz_sections("japan")
    content += "## Collab & Event Calendar\n\n" + render_events_table(events) + "\n"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "japan.md").write_text(content, encoding="utf-8")
    return content


def update_readme():
    readme_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    for region in ("global", "japan"):
        for category, _label in CATEGORIES:
            trend = load_json(DATA_TRENDS_DIR / f"{region}-{category}-7d.json", default={"entries": []})
            readme_text = replace_marker_section(
                readme_text, f"{region}-{category}-top5", render_trend_table(trend["entries"], limit=5)
            )
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    readme_text = replace_marker_section(readme_text, "last-updated", f"Last updated: {timestamp}")

    README_PATH.write_text(readme_text, encoding="utf-8")
    return readme_text


def run():
    render_global_report()
    render_japan_report()
    update_readme()


if __name__ == "__main__":
    run()
