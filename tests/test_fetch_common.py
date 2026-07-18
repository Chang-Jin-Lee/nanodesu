from unittest.mock import patch, MagicMock
import requests
import pytest

from scripts.fetch.common import fetch_url, FetchError, DEFAULT_USER_AGENT


def _mock_response(text, status_ok=True):
    resp = MagicMock()
    resp.text = text
    if status_ok:
        resp.raise_for_status = MagicMock()
    else:
        resp.raise_for_status = MagicMock(side_effect=requests.HTTPError("500"))
    return resp


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_returns_text_on_success(mock_get):
    mock_get.return_value = _mock_response("hello world")
    result = fetch_url("https://example.com/feed")
    assert result == "hello world"


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_sends_default_user_agent(mock_get):
    mock_get.return_value = _mock_response("ok")
    fetch_url("https://example.com/feed")
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["User-Agent"] == DEFAULT_USER_AGENT


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_merges_extra_headers(mock_get):
    mock_get.return_value = _mock_response("ok")
    fetch_url("https://example.com/feed", headers={"Accept": "application/xml"})
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Accept"] == "application/xml"
    assert kwargs["headers"]["User-Agent"] == DEFAULT_USER_AGENT


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_retries_then_succeeds(mock_get):
    mock_get.side_effect = [
        requests.ConnectionError("boom"),
        _mock_response("recovered"),
    ]
    result = fetch_url("https://example.com/feed", max_retries=3, backoff_seconds=0)
    assert result == "recovered"
    assert mock_get.call_count == 2


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_raises_fetch_error_after_exhausting_retries(mock_get):
    mock_get.side_effect = requests.ConnectionError("boom")
    with pytest.raises(FetchError):
        fetch_url("https://example.com/feed", max_retries=2, backoff_seconds=0)
    assert mock_get.call_count == 2


@patch("scripts.fetch.common.requests.get")
def test_fetch_url_ignores_caller_supplied_user_agent_override(mock_get):
    mock_get.return_value = _mock_response("ok")
    fetch_url("https://example.com/feed", headers={"User-Agent": "evil-bot/1.0"})
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["User-Agent"] == DEFAULT_USER_AGENT
