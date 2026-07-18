from unittest.mock import patch

from scripts.fetch.rss import parse_feed_text, fetch_rss

SAMPLE_RSS_2_0 = """<?xml version="1.0" encoding="utf-8" ?>
<rss version="2.0">
  <channel>
    <title>Anime News Network</title>
    <link>https://www.animenewsnetwork.com/</link>
    <item>
      <title>Jump Magazine Apologizes to Fans Unable to Buy Issue With Blue Box Finale, One Piece Card</title>
      <link>https://www.animenewsnetwork.com/interest/2026-07-17/jump-magazine-apologizes/.239691</link>
      <description>Apologies come after issue sells out in stores</description>
      <pubDate>Fri, 17 Jul 2026 23:59:00 -0400</pubDate>
      <category>Manga</category>
    </item>
    <item>
      <title>An Older Eri Thanks Her Heroes in My Hero Academia Short</title>
      <link>https://www.animenewsnetwork.com/conv/eri-short/.239690</link>
      <description>A new short debuts</description>
      <pubDate>Fri, 17 Jul 2026 16:00:00 -0400</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>RPG Site</title>
  <entry>
    <title>Wuthering Waves Version 2.5 Detailed</title>
    <link href="https://rpgsite.net/news/wuwa-25" />
    <updated>2026-07-16T10:00:00Z</updated>
    <summary>New banners and a story chapter arrive.</summary>
  </entry>
</feed>
"""


def test_parse_feed_text_extracts_rss_2_0_items():
    items = parse_feed_text(SAMPLE_RSS_2_0, source="ann", region="global")
    assert len(items) == 2
    first = items[0]
    assert first["title"].startswith("Jump Magazine Apologizes")
    assert first["url"] == "https://www.animenewsnetwork.com/interest/2026-07-17/jump-magazine-apologizes/.239691"
    assert first["published"] == "2026-07-18"
    assert first["source"] == "ann"
    assert first["region"] == "global"
    assert "Apologies" in first["summary"]


def test_parse_feed_text_extracts_atom_items():
    items = parse_feed_text(SAMPLE_ATOM, source="rpgsite", region="global")
    assert len(items) == 1
    assert items[0]["title"] == "Wuthering Waves Version 2.5 Detailed"
    assert items[0]["url"] == "https://rpgsite.net/news/wuwa-25"
    assert items[0]["published"] == "2026-07-16"


def test_parse_feed_text_skips_entries_without_link():
    broken = SAMPLE_RSS_2_0.replace(
        "<link>https://www.animenewsnetwork.com/interest/2026-07-17/jump-magazine-apologizes/.239691</link>",
        "",
    )
    items = parse_feed_text(broken, source="ann", region="global")
    assert len(items) == 1


@patch("scripts.fetch.rss.fetch_url")
def test_fetch_rss_calls_fetch_url_and_parses(mock_fetch_url):
    mock_fetch_url.return_value = SAMPLE_RSS_2_0
    items = fetch_rss("https://www.animenewsnetwork.com/all/rss.xml", source="ann", region="global")
    assert len(items) == 2
    mock_fetch_url.assert_called_once()
    args, kwargs = mock_fetch_url.call_args
    assert args[0] == "https://www.animenewsnetwork.com/all/rss.xml"
