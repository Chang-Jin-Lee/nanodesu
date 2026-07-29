# tests/test_fetch_all.py
import json
from unittest.mock import patch

import pytest

import scripts.fetch_all as fetch_all


SAMPLE_CONFIG = {
    "sources": [
        {"slug": "ann", "type": "rss", "region": "global", "url": "https://example.com/ann.xml"},
        {"slug": "reddit_manga", "type": "rss", "region": "global", "url": "https://example.com/manga.rss", "category": "manga"},
        {"slug": "flaky", "type": "rss", "region": "global", "url": "https://example.com/flaky.xml", "optional": True},
    ],
    "steam_titles": [{"appid": 999, "title": "Test Game"}],
    "anilist": {"enabled": True},
    "magazines": {"enabled": True},
    "events": {"collabocafe": {"enabled": True}},
}


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_all, "DATA_RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(fetch_all, "DATA_EVENTS_DIR", tmp_path / "data" / "events")
    monkeypatch.setattr(fetch_all, "STATUS_PATH", tmp_path / "data" / "status.json")
    return tmp_path


@patch("scripts.fetch_all.fetch_collabocafe_events")
@patch("scripts.fetch_all.fetch_all_magazines")
@patch("scripts.fetch_all.fetch_steam_news")
@patch("scripts.fetch_all.fetch_trending_anime")
@patch("scripts.fetch_all.fetch_rss")
def test_run_writes_raw_json_per_source_and_status(
    mock_fetch_rss, mock_anilist, mock_steam, mock_magazines, mock_events, tmp_repo
):
    mock_fetch_rss.side_effect = [
        [{"title": "A", "url": "u", "published": "2026-07-18", "source": "ann", "region": "global", "category": None, "summary": ""}],
        [{"title": "M", "url": "u", "published": "2026-07-18", "source": "reddit_manga", "region": "global", "category": "manga", "summary": ""}],
        RuntimeError("network down"),
    ]
    mock_anilist.return_value = [{"title": "B", "trending_score": 1, "popularity": 1, "site_url": "u"}]
    mock_steam.return_value = [{"title": "C", "url": "u", "published": "2026-07-18", "source": "steam-999", "region": "global", "summary": ""}]
    mock_magazines.return_value = [{"title": "D", "url": "u", "published": "2026-07-18", "source": "shonenjump", "region": "japan", "summary": ""}]
    mock_events.return_value = [{"title": "E", "url": "u", "venue": "", "start_date": None, "end_date": None, "category": "", "description": "", "source_site": "collabocafe"}]

    status = fetch_all.run(config=SAMPLE_CONFIG, date_str="2026-07-18")

    assert status["ann"]["ok"] is True
    assert status["ann"]["count"] == 1
    assert status["flaky"]["ok"] is False
    assert status["flaky"]["optional"] is True
    assert status["anilist"]["ok"] is True
    assert status["steam-999"]["ok"] is True
    assert status["magazines"]["ok"] is True
    assert status["collabocafe"]["ok"] is True

    ann_file = tmp_repo / "data" / "raw" / "ann" / "2026-07-18.json"
    assert ann_file.exists()
    assert json.loads(ann_file.read_text(encoding="utf-8"))[0]["title"] == "A"

    status_file = tmp_repo / "data" / "status.json"
    assert status_file.exists()


@patch("scripts.fetch_all.fetch_collabocafe_events")
@patch("scripts.fetch_all.fetch_all_magazines")
@patch("scripts.fetch_all.fetch_steam_news")
@patch("scripts.fetch_all.fetch_trending_anime")
@patch("scripts.fetch_all.fetch_rss")
def test_run_never_raises_when_a_required_source_fails(
    mock_fetch_rss, mock_anilist, mock_steam, mock_magazines, mock_events, tmp_repo
):
    mock_fetch_rss.side_effect = RuntimeError("boom")
    mock_anilist.return_value = []
    mock_steam.return_value = []
    mock_magazines.return_value = []
    mock_events.return_value = []

    status = fetch_all.run(config=SAMPLE_CONFIG, date_str="2026-07-18")
    assert status["ann"]["ok"] is False


@patch("scripts.fetch_all.fetch_collabocafe_events")
@patch("scripts.fetch_all.fetch_all_magazines")
@patch("scripts.fetch_all.fetch_steam_news")
@patch("scripts.fetch_all.fetch_trending_anime")
@patch("scripts.fetch_all.fetch_rss")
def test_run_passes_source_category_to_fetch_rss(
    mock_fetch_rss, mock_anilist, mock_steam, mock_magazines, mock_events, tmp_repo
):
    mock_fetch_rss.return_value = []
    mock_anilist.return_value = []
    mock_steam.return_value = []
    mock_magazines.return_value = []
    mock_events.return_value = []

    fetch_all.run(config=SAMPLE_CONFIG, date_str="2026-07-18")

    categories = {c.kwargs["source"]: c.kwargs["category"] for c in mock_fetch_rss.call_args_list}
    assert categories["reddit_manga"] == "manga"
    assert categories["ann"] is None
