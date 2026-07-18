from unittest.mock import patch

from scripts.fetch.steam_news import steam_news_url, fetch_steam_news


def test_steam_news_url_builds_expected_feed_path():
    assert steam_news_url(4162040) == "https://store.steampowered.com/feeds/news/app/4162040/"


@patch("scripts.fetch.steam_news.fetch_rss")
def test_fetch_steam_news_uses_appid_slug_and_tags_watch_title(mock_fetch_rss):
    mock_fetch_rss.return_value = [
        {"title": "Patch 3.1 notes", "url": "https://x", "published": "2026-07-17", "source": "steam-4162040", "region": "global", "summary": ""}
    ]
    items = fetch_steam_news(4162040, "Zenless Zone Zero")
    assert len(items) == 1
    assert items[0]["watch_title_hint"] == "Zenless Zone Zero"
    mock_fetch_rss.assert_called_once_with(
        "https://store.steampowered.com/feeds/news/app/4162040/",
        source="steam-4162040",
        region="global",
    )
