from pathlib import Path
from unittest.mock import patch, call

from scripts.fetch.scrape_magazines import (
    parse_shonenjump_html,
    parse_shonenmagazine_html,
    parse_websunday_html,
    fetch_all_magazines,
    SHONENJUMP_URL,
    SHONENMAGAZINE_URL,
    WEBSUNDAY_URL,
)
from scripts.fetch.common import FetchError

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_shonenjump_html_extracts_items_with_dates_stripped_from_title():
    html = (FIXTURES / "shonenjump_sample.html").read_text(encoding="utf-8")
    items = parse_shonenjump_html(html)
    assert len(items) == 2
    first = items[0]
    assert first["published"] == "2026-07-13"
    assert "2026/07/13" not in first["title"]
    assert first["title"].startswith("週刊少年ジャンプ33号の表紙が")
    assert first["url"] == "https://www.shonenjump.com/j/teikikoudoku/"
    assert first["source"] == "shonenjump"
    assert first["region"] == "japan"


def test_parse_shonenmagazine_html_extracts_date_from_entry_url_slug():
    html = (FIXTURES / "shonenmagazine_sample.html").read_text(encoding="utf-8")
    items = parse_shonenmagazine_html(html)
    assert len(items) == 2
    first = items[0]
    assert first["title"] == "『GTO』ドラマ化記念！藤沢とおるワールドをイッキ読み！"
    assert first["published"] == "2026-07-17"
    assert first["summary"].startswith("7月18日限定で")
    assert first["source"] == "shonenmagazine"


def test_parse_websunday_html_extracts_item_with_relative_url_resolved():
    html = (FIXTURES / "websunday_sample.html").read_text(encoding="utf-8")
    items = parse_websunday_html(html)
    assert len(items) == 1
    assert items[0]["title"] == "少年サンデー33号発売中！　デジタル版も同時発売!!"
    assert items[0]["published"] == "2026-07-15"
    assert items[0]["url"] == "https://websunday.net/95244/"
    assert items[0]["source"] == "websunday"


@patch("scripts.fetch.scrape_magazines.fetch_url")
def test_fetch_all_magazines_fetches_all_three_sites(mock_fetch_url):
    mock_fetch_url.side_effect = [
        (FIXTURES / "shonenjump_sample.html").read_text(encoding="utf-8"),
        (FIXTURES / "shonenmagazine_sample.html").read_text(encoding="utf-8"),
        (FIXTURES / "websunday_sample.html").read_text(encoding="utf-8"),
    ]
    items = fetch_all_magazines()
    assert len(items) == 5
    mock_fetch_url.assert_has_calls(
        [call(SHONENJUMP_URL), call(SHONENMAGAZINE_URL), call(WEBSUNDAY_URL)]
    )


def test_parse_shonenjump_html_marks_items_as_manga():
    html = (FIXTURES / "shonenjump_sample.html").read_text(encoding="utf-8")
    items = parse_shonenjump_html(html)
    assert all(item["category"] == "manga" for item in items)


def test_parse_shonenmagazine_html_marks_items_as_manga():
    html = (FIXTURES / "shonenmagazine_sample.html").read_text(encoding="utf-8")
    items = parse_shonenmagazine_html(html)
    assert all(item["category"] == "manga" for item in items)


def test_parse_websunday_html_marks_items_as_manga():
    html = (FIXTURES / "websunday_sample.html").read_text(encoding="utf-8")
    items = parse_websunday_html(html)
    assert all(item["category"] == "manga" for item in items)


@patch("scripts.fetch.scrape_magazines.fetch_url")
def test_fetch_all_magazines_keeps_going_when_one_site_fails(mock_fetch_url):
    mock_fetch_url.side_effect = [
        FetchError("404 Client Error"),
        (FIXTURES / "shonenmagazine_sample.html").read_text(encoding="utf-8"),
        (FIXTURES / "websunday_sample.html").read_text(encoding="utf-8"),
    ]
    items = fetch_all_magazines()
    sources = {item["source"] for item in items}
    assert sources == {"shonenmagazine", "websunday"}
    assert mock_fetch_url.call_count == 3


@patch("scripts.fetch.scrape_magazines.fetch_url")
def test_fetch_all_magazines_skips_a_site_whose_parser_raises(mock_fetch_url):
    mock_fetch_url.side_effect = [
        "<html>totally unexpected markup</html>",
        (FIXTURES / "shonenmagazine_sample.html").read_text(encoding="utf-8"),
        (FIXTURES / "websunday_sample.html").read_text(encoding="utf-8"),
    ]
    items = fetch_all_magazines()
    assert {item["source"] for item in items} == {"shonenmagazine", "websunday"}
