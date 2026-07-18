# tests/test_fetch_anilist.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests

from scripts.fetch.anilist import parse_anilist_response, fetch_trending_anime, ANILIST_API_URL
from scripts.fetch.common import DEFAULT_USER_AGENT

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "anilist_trending_sample.json"


def test_parse_anilist_response_prefers_english_title():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    entries = parse_anilist_response(payload)
    assert entries[0]["title"] == "That Time I Got Reincarnated as a Slime Season 4"
    assert entries[0]["trending_score"] == 685
    assert entries[0]["popularity"] == 116158
    assert entries[0]["site_url"] == "https://anilist.co/anime/182205"


def test_parse_anilist_response_falls_back_to_romaji_when_english_missing():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    entries = parse_anilist_response(payload)
    assert entries[1]["title"].startswith("Hell Mode")


def test_parse_anilist_response_handles_empty_media():
    entries = parse_anilist_response({"data": {"Page": {"media": []}}})
    assert entries == []


def test_parse_anilist_response_handles_null_data():
    assert parse_anilist_response({"data": None, "errors": [{"message": "rate limited"}]}) == []


def test_parse_anilist_response_handles_null_page():
    assert parse_anilist_response({"data": {"Page": None}}) == []


def test_parse_anilist_response_handles_null_media():
    assert parse_anilist_response({"data": {"Page": {"media": None}}}) == []


@patch("scripts.fetch.anilist.requests.post")
def test_fetch_trending_anime_posts_graphql_query(mock_post):
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    entries = fetch_trending_anime(per_page=3)

    assert len(entries) == 3
    args, kwargs = mock_post.call_args
    assert args[0] == ANILIST_API_URL
    assert kwargs["json"]["variables"]["perPage"] == 3


@patch("scripts.fetch.anilist.requests.post")
def test_fetch_trending_anime_sends_default_user_agent(mock_post):
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    fetch_trending_anime(per_page=3)

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["User-Agent"] == DEFAULT_USER_AGENT


@patch("scripts.fetch.anilist.requests.post")
def test_fetch_trending_anime_retries_then_succeeds(mock_post):
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()

    mock_post.side_effect = [requests.ConnectionError("boom"), mock_response]

    entries = fetch_trending_anime(per_page=3, backoff_seconds=0)

    assert len(entries) == 3
    assert mock_post.call_count == 2
