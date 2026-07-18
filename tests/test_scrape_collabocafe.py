from pathlib import Path
from unittest.mock import patch

from scripts.fetch.scrape_collabocafe import (
    parse_event_period,
    parse_venue,
    parse_collabocafe_html,
    fetch_collabocafe_events,
    COLLABOCAFE_URL,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "collabocafe_sample.html"


def test_parse_event_period_normal_range_same_year():
    start, end = parse_event_period("期間 : 2026年7月23日〜8月23日")
    assert start == "2026-07-23"
    assert end == "2026-08-23"


def test_parse_event_period_range_crossing_year_boundary():
    start, end = parse_event_period("期間 : 2026年10月30日〜1月11日")
    assert start == "2026-10-30"
    assert end == "2027-01-11"


def test_parse_event_period_open_ended():
    start, end = parse_event_period("期間 : 2026年7月24日〜")
    assert start == "2026-07-24"
    assert end is None


def test_parse_event_period_deadline_only():
    start, end = parse_event_period("～2026年8月8日まで予約受付")
    assert start is None
    assert end == "2026-08-08"


def test_parse_event_period_no_match_returns_none_none():
    assert parse_event_period("") == (None, None)
    assert parse_event_period("no date here") == (None, None)


def test_parse_venue_extracts_text_after_in():
    assert parse_venue("ハイキュー!!展 挑戦者たち in 六本木 10月30日より開催!") == "六本木"


def test_parse_venue_returns_empty_when_no_in_keyword():
    assert parse_venue("ウマ娘シングレ 熱いレースシーンを再現! 描き下ろしグッズが登場") == ""


def test_parse_collabocafe_html_extracts_all_events():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    events = parse_collabocafe_html(html)
    assert len(events) == 4

    normal_range = events[0]
    assert normal_range["title"] == "すみっコぐらし カフェ in タワレコカフェ表参道 7月23日より開催!"
    assert normal_range["url"].startswith("https://collabo-cafe.com/events/collabo/sumikko-gurashi")
    assert normal_range["venue"] == "タワレコカフェ表参道"
    assert normal_range["start_date"] == "2026-07-23"
    assert normal_range["end_date"] == "2026-08-23"
    assert normal_range["category"] == "ニュース"
    assert normal_range["source_site"] == "collabocafe"

    deadline_only = events[3]
    assert deadline_only["start_date"] is None
    assert deadline_only["end_date"] == "2026-08-08"


@patch("scripts.fetch.scrape_collabocafe.fetch_url")
def test_fetch_collabocafe_events_calls_fetch_url_with_homepage(mock_fetch_url):
    mock_fetch_url.return_value = FIXTURE_PATH.read_text(encoding="utf-8")
    events = fetch_collabocafe_events()
    assert len(events) == 4
    mock_fetch_url.assert_called_once_with(COLLABOCAFE_URL)
