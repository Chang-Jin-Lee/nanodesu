import json
from datetime import date

from scripts.render_reports import (
    render_trend_table,
    render_anilist_table,
    render_events_table,
    replace_marker_section,
    render_global_report,
    render_japan_report,
    update_readme,
    format_delta,
)
import scripts.render_reports as render_reports


TREND_ENTRIES = [
    {"title": "ONE PIECE", "mentions": 5, "sources": ["ann", "gematsu"], "delta": 2},
    {"title": "Haikyu!!", "mentions": 2, "sources": ["ann"], "delta": None},
]

GAME_TREND_ENTRIES = [
    {"title": "Genshin Impact", "mentions": 4, "sources": ["gematsu"], "delta": 1},
]

TREND_ENTRIES_WITH_DELTA = [
    {"title": "ONE PIECE", "mentions": 5, "sources": ["ann", "gematsu"], "delta": 2},
    {"title": "Haikyu!!", "mentions": 3, "sources": ["ann"], "delta": -1},
    {"title": "Chainsaw Man", "mentions": 2, "sources": ["ann"], "delta": 0},
    {"title": "New Show", "mentions": 1, "sources": ["ann"], "delta": None},
]

ANILIST_ENTRIES = [
    {"title": "Slime Season 4", "trending_score": 685, "popularity": 116158, "site_url": "https://anilist.co/anime/182205"},
]

EVENT_ENTRIES = [
    {"title": "Cafe A", "venue": "Shibuya", "start_date": "2026-07-20", "end_date": "2026-08-01", "url": "https://x"},
]

MANGA_TREND_ENTRIES = [
    {"title": "Kagurabachi", "mentions": 3, "sources": ["shonenjump"], "delta": None},
]

ANILIST_MANGA_ENTRIES = [
    {"title": "Kagurabachi", "trending_score": 400, "popularity": 50000, "site_url": "https://anilist.co/manga/151514"},
]


def _write_trend_files(trends_dir, region, anime_entries, game_entries, manga_entries=None):
    manga_entries = manga_entries if manga_entries is not None else []
    for window in (7, 30):
        (trends_dir / f"{region}-anime-{window}d.json").write_text(
            json.dumps({"entries": anime_entries}), encoding="utf-8"
        )
        (trends_dir / f"{region}-manga-{window}d.json").write_text(
            json.dumps({"entries": manga_entries}), encoding="utf-8"
        )
        (trends_dir / f"{region}-game-{window}d.json").write_text(
            json.dumps({"entries": game_entries}), encoding="utf-8"
        )


def test_render_trend_table_produces_markdown_rows():
    table = render_trend_table(TREND_ENTRIES)
    assert "| 1 | ONE PIECE | 5 | ▲2 | ann, gematsu |" in table
    assert "| 2 | Haikyu!! | 2 | NEW | ann |" in table


def test_render_trend_table_respects_limit():
    table = render_trend_table(TREND_ENTRIES, limit=1)
    assert "ONE PIECE" in table
    assert "Haikyu!!" not in table


def test_render_trend_table_handles_empty_entries():
    assert "No data yet" in render_trend_table([])


def test_format_delta_formats_all_four_cases():
    assert format_delta(2) == "▲2"
    assert format_delta(-1) == "▼1"
    assert format_delta(0) == "-"
    assert format_delta(None) == "NEW"


def test_render_trend_table_includes_delta_column():
    table = render_trend_table(TREND_ENTRIES_WITH_DELTA)
    assert "| # | Title | Mentions | Δ | Sources |" in table
    assert "| 1 | ONE PIECE | 5 | ▲2 | ann, gematsu |" in table
    assert "| 2 | Haikyu!! | 3 | ▼1 | ann |" in table
    assert "| 3 | Chainsaw Man | 2 | - | ann |" in table
    assert "| 4 | New Show | 1 | NEW | ann |" in table


def test_render_anilist_table_links_title_to_site_url():
    table = render_anilist_table(ANILIST_ENTRIES)
    assert "[Slime Season 4](https://anilist.co/anime/182205)" in table
    assert "685" in table


def test_render_events_table_includes_venue_and_dates():
    table = render_events_table(EVENT_ENTRIES)
    assert "Cafe A" in table
    assert "Shibuya" in table
    assert "2026-07-20" in table
    assert "2026-08-01" in table


def test_render_events_table_handles_empty_events():
    assert "No upcoming events" in render_events_table([])


def test_replace_marker_section_replaces_existing_content():
    readme = "before\n<!--START_SECTION:demo-->old<!--END_SECTION:demo-->\nafter"
    updated = replace_marker_section(readme, "demo", "new")
    assert "old" not in updated
    assert "<!--START_SECTION:demo-->\nnew\n<!--END_SECTION:demo-->" in updated
    assert updated.startswith("before")
    assert updated.endswith("after")


def test_replace_marker_section_appends_when_markers_absent():
    readme = "just some readme text"
    updated = replace_marker_section(readme, "demo", "new content")
    assert "<!--START_SECTION:demo-->" in updated
    assert "new content" in updated


def test_render_global_report_writes_anime_manga_and_game_sections(tmp_path, monkeypatch):
    trends_dir = tmp_path / "trends"
    trends_dir.mkdir()
    _write_trend_files(trends_dir, "global", TREND_ENTRIES, GAME_TREND_ENTRIES, MANGA_TREND_ENTRIES)
    raw_dir = tmp_path / "raw"
    (raw_dir / "anilist").mkdir(parents=True)
    (raw_dir / "anilist" / "2026-07-18.json").write_text(json.dumps(ANILIST_ENTRIES), encoding="utf-8")
    (raw_dir / "anilist-manga").mkdir(parents=True)
    (raw_dir / "anilist-manga" / "2026-07-18.json").write_text(json.dumps(ANILIST_MANGA_ENTRIES), encoding="utf-8")
    reports_dir = tmp_path / "reports"

    monkeypatch.setattr(render_reports, "DATA_TRENDS_DIR", trends_dir)
    monkeypatch.setattr(render_reports, "DATA_RAW_DIR", raw_dir)
    monkeypatch.setattr(render_reports, "REPORTS_DIR", reports_dir)

    content = render_global_report()
    assert "## AniList Trending Anime" in content
    assert "## AniList Trending Manga" in content
    assert "Slime Season 4" in content
    assert "[Kagurabachi](https://anilist.co/manga/151514)" in content
    for window in (7, 30):
        assert f"## Anime Buzz — Last {window} Days" in content
        assert f"## Manga Buzz — Last {window} Days" in content
        assert f"## Game Buzz — Last {window} Days" in content
    assert content.index("Anime Buzz — Last 7 Days") < content.index("Manga Buzz — Last 7 Days")
    assert content.index("Manga Buzz — Last 7 Days") < content.index("Game Buzz — Last 7 Days")
    assert content.index("Game Buzz — Last 7 Days") < content.index("Anime Buzz — Last 30 Days")
    assert "ONE PIECE" in content
    assert "Genshin Impact" in content
    assert (reports_dir / "global.md").exists()


def test_render_japan_report_includes_categories_and_events(tmp_path, monkeypatch):
    trends_dir = tmp_path / "trends"
    trends_dir.mkdir()
    _write_trend_files(trends_dir, "japan", [], GAME_TREND_ENTRIES, MANGA_TREND_ENTRIES)
    events_path = tmp_path / "events.json"
    events_path.write_text(json.dumps(EVENT_ENTRIES), encoding="utf-8")
    reports_dir = tmp_path / "reports"

    monkeypatch.setattr(render_reports, "DATA_TRENDS_DIR", trends_dir)
    monkeypatch.setattr(render_reports, "DATA_EVENTS_PATH", events_path)
    monkeypatch.setattr(render_reports, "REPORTS_DIR", reports_dir)

    content = render_japan_report()
    assert "## Anime Buzz — Last 7 Days" in content
    assert "## Manga Buzz — Last 7 Days" in content
    assert "## Game Buzz — Last 7 Days" in content
    assert "## Collab & Event Calendar" in content
    assert "Kagurabachi" in content
    assert "Genshin Impact" in content
    assert "Cafe A" in content
    assert (reports_dir / "japan.md").exists()


def test_update_readme_replaces_six_category_markers(tmp_path, monkeypatch):
    trends_dir = tmp_path / "trends"
    trends_dir.mkdir()
    _write_trend_files(trends_dir, "global", TREND_ENTRIES, GAME_TREND_ENTRIES, MANGA_TREND_ENTRIES)
    _write_trend_files(trends_dir, "japan", [], [], [])
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "# nanodesu\n"
        "<!--START_SECTION:global-anime-top5--><!--END_SECTION:global-anime-top5-->\n"
        "<!--START_SECTION:global-manga-top5--><!--END_SECTION:global-manga-top5-->\n"
        "<!--START_SECTION:global-game-top5--><!--END_SECTION:global-game-top5-->\n"
        "<!--START_SECTION:japan-anime-top5--><!--END_SECTION:japan-anime-top5-->\n"
        "<!--START_SECTION:japan-manga-top5--><!--END_SECTION:japan-manga-top5-->\n"
        "<!--START_SECTION:japan-game-top5--><!--END_SECTION:japan-game-top5-->\n"
        "<!--START_SECTION:last-updated--><!--END_SECTION:last-updated-->\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(render_reports, "DATA_TRENDS_DIR", trends_dir)
    monkeypatch.setattr(render_reports, "README_PATH", readme_path)

    updated = update_readme()

    def body(name):
        return updated.split(f"<!--START_SECTION:{name}-->")[1].split(f"<!--END_SECTION:{name}-->")[0]

    assert "ONE PIECE" in body("global-anime-top5")
    assert "Kagurabachi" in body("global-manga-top5")
    assert "Genshin Impact" in body("global-game-top5")
    assert "No data yet" in body("japan-manga-top5")
    assert "Last updated:" in updated
    # The manga markers must already exist in the file, not be appended at the end.
    assert updated.index("global-manga-top5") < updated.index("global-game-top5")
