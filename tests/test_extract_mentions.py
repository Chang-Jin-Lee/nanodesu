# tests/test_extract_mentions.py
import json

from scripts.extract_mentions import (
    load_watchlist,
    find_mentions,
    extract_mentions_from_items,
    collect_items_for_date,
    run,
)

SAMPLE_WATCHLIST = [
    ("ONE PIECE", ["ONE PIECE", "ワンピース"], "anime"),
    ("Haikyu!!", ["Haikyu!!", "ハイキュー"], "anime"),
    ("Genshin Impact", ["Genshin Impact", "原神"], "game"),
]


def test_load_watchlist_reads_canonical_aliases_and_category(tmp_path):
    path = tmp_path / "watchlist.yaml"
    path.write_text(
        "titles:\n"
        "  - canonical: \"ONE PIECE\"\n"
        "    category: anime\n"
        "    aliases: [\"ワンピース\"]\n"
        "  - canonical: \"Genshin Impact\"\n"
        "    category: game\n"
        "    aliases: []\n",
        encoding="utf-8",
    )
    watchlist = load_watchlist(path)
    assert watchlist == [
        ("ONE PIECE", ["ONE PIECE", "ワンピース"], "anime"),
        ("Genshin Impact", ["Genshin Impact"], "game"),
    ]


def test_load_watchlist_defaults_missing_category_to_anime(tmp_path):
    path = tmp_path / "watchlist.yaml"
    path.write_text(
        "titles:\n  - canonical: \"ONE PIECE\"\n    aliases: []\n",
        encoding="utf-8",
    )
    assert load_watchlist(path) == [("ONE PIECE", ["ONE PIECE"], "anime")]


def test_find_mentions_matches_alias_and_canonical():
    assert find_mentions("ハイキュー!!展 挑戦者たち in 六本木", SAMPLE_WATCHLIST) == ["Haikyu!!"]
    assert find_mentions("週刊少年ジャンプ「ONE PIECE」新連載29周年", SAMPLE_WATCHLIST) == ["ONE PIECE"]


def test_find_mentions_returns_empty_when_no_match():
    assert find_mentions("Completely unrelated headline", SAMPLE_WATCHLIST) == []


def test_find_mentions_short_ascii_alias_does_not_match_inside_longer_word():
    watchlist = [("GTO", ["GTO", "グレート・ティーチャー・オニヅカ"], "anime")]
    assert find_mentions("MAGTOOL discount sale", watchlist) == []


def test_find_mentions_short_ascii_alias_matches_as_standalone_word():
    watchlist = [("GTO", ["GTO", "グレート・ティーチャー・オニヅカ"], "anime")]
    assert find_mentions("GTO drama announced", watchlist) == ["GTO"]
    assert find_mentions("『GTO』ドラマ化記念", watchlist) == ["GTO"]


def test_find_mentions_japanese_only_alias_still_matches_via_substring():
    watchlist = [("GTO", ["GTO", "グレート・ティーチャー・オニヅカ"], "anime")]
    assert find_mentions("グレート・ティーチャー・オニヅカ最新情報", watchlist) == ["GTO"]


def test_find_mentions_matches_mixed_script_alias_case_insensitively():
    watchlist = [("Spy x Family", ["Spy x Family", "SPY×FAMILY", "スパイファミリー"], "anime")]
    assert find_mentions("Spy×Family Season 3 announced", watchlist) == ["Spy x Family"]
    assert find_mentions("spy×family season 3", watchlist) == ["Spy x Family"]


def test_extract_mentions_from_items_builds_mention_records():
    items = [
        {"title": "ONE PIECE 連載29周年を祝う", "url": "https://x/1", "published": "2026-07-17", "source": "ann", "region": "global"},
        {"title": "Genshin Impact 6.0 update", "url": "https://x/2", "published": "2026-07-17", "source": "gematsu", "region": "global"},
        {"title": "unrelated headline", "url": "https://x/3", "published": "2026-07-17", "source": "ann", "region": "global"},
    ]
    mentions = extract_mentions_from_items(items, SAMPLE_WATCHLIST)
    assert len(mentions) == 2
    assert mentions[0] == {
        "watch_title": "ONE PIECE",
        "category": "anime",
        "region": "global",
        "date": "2026-07-17",
        "source": "ann",
        "item_url": "https://x/1",
    }
    assert mentions[1]["watch_title"] == "Genshin Impact"
    assert mentions[1]["category"] == "game"


def test_extract_mentions_from_items_uses_item_category_when_present():
    items = [
        {"title": "ONE PIECE 最新話", "url": "https://x/1", "published": "2026-07-17", "source": "shonenjump", "region": "japan", "category": "manga"},
    ]
    mentions = extract_mentions_from_items(items, SAMPLE_WATCHLIST)
    assert mentions[0]["category"] == "manga"


def test_extract_mentions_from_items_falls_back_to_title_category_when_item_has_none():
    items = [
        {"title": "ONE PIECE 連載29周年", "url": "https://x/1", "published": "2026-07-17", "source": "ann", "region": "global", "category": None},
        {"title": "Genshin Impact 6.0 update", "url": "https://x/2", "published": "2026-07-17", "source": "ann", "region": "global"},
    ]
    mentions = extract_mentions_from_items(items, SAMPLE_WATCHLIST)
    assert mentions[0]["category"] == "anime"
    assert mentions[1]["category"] == "game"


def test_collect_items_for_date_skips_anilist_manga_source(tmp_path):
    raw_dir = tmp_path / "raw"
    (raw_dir / "ann").mkdir(parents=True)
    (raw_dir / "anilist-manga").mkdir(parents=True)
    (raw_dir / "ann" / "2026-07-18.json").write_text(
        json.dumps([{"title": "A", "url": "u1", "published": "2026-07-18", "source": "ann", "region": "global"}]),
        encoding="utf-8",
    )
    (raw_dir / "anilist-manga" / "2026-07-18.json").write_text(
        json.dumps([{"title": "ONE PIECE", "native_title": "ワンピース", "romaji_title": "ONE PIECE", "trending_score": 99, "popularity": 1000, "site_url": "https://anilist/1"}]),
        encoding="utf-8",
    )
    items = collect_items_for_date("2026-07-18", raw_dir=raw_dir)
    titles = {item["title"] for item in items}
    assert titles == {"A"}


def test_collect_items_for_date_reads_all_source_files_for_that_date(tmp_path):
    raw_dir = tmp_path / "raw"
    (raw_dir / "ann").mkdir(parents=True)
    (raw_dir / "gematsu").mkdir(parents=True)
    (raw_dir / "ann" / "2026-07-18.json").write_text(
        json.dumps([{"title": "A", "url": "u1", "published": "2026-07-18", "source": "ann", "region": "global"}]),
        encoding="utf-8",
    )
    (raw_dir / "gematsu" / "2026-07-18.json").write_text(
        json.dumps([{"title": "B", "url": "u2", "published": "2026-07-18", "source": "gematsu", "region": "global"}]),
        encoding="utf-8",
    )
    (raw_dir / "ann" / "2026-07-17.json").write_text(
        json.dumps([{"title": "C", "url": "u3", "published": "2026-07-17", "source": "ann", "region": "global"}]),
        encoding="utf-8",
    )
    items = collect_items_for_date("2026-07-18", raw_dir=raw_dir)
    titles = {item["title"] for item in items}
    assert titles == {"A", "B"}


def test_collect_items_for_date_skips_anilist_source(tmp_path):
    raw_dir = tmp_path / "raw"
    (raw_dir / "ann").mkdir(parents=True)
    (raw_dir / "anilist").mkdir(parents=True)
    (raw_dir / "ann" / "2026-07-18.json").write_text(
        json.dumps([{"title": "A", "url": "u1", "published": "2026-07-18", "source": "ann", "region": "global"}]),
        encoding="utf-8",
    )
    (raw_dir / "anilist" / "2026-07-18.json").write_text(
        json.dumps([{"title": "ONE PIECE", "trending_score": 99, "popularity": 1000, "site_url": "https://anilist/1"}]),
        encoding="utf-8",
    )
    items = collect_items_for_date("2026-07-18", raw_dir=raw_dir)
    titles = {item["title"] for item in items}
    assert titles == {"A"}


def test_run_writes_mentions_file_for_the_date(tmp_path):
    raw_dir = tmp_path / "raw"
    (raw_dir / "ann").mkdir(parents=True)
    (raw_dir / "ann" / "2026-07-18.json").write_text(
        json.dumps([{"title": "ONE PIECE special", "url": "u1", "published": "2026-07-18", "source": "ann", "region": "global"}]),
        encoding="utf-8",
    )
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(
        "titles:\n  - canonical: \"ONE PIECE\"\n    aliases: []\n", encoding="utf-8"
    )
    mentions_dir = tmp_path / "mentions"

    mentions = run("2026-07-18", watchlist_path=watchlist_path, raw_dir=raw_dir, mentions_dir=mentions_dir)

    assert len(mentions) == 1
    assert mentions[0]["category"] == "anime"
    out_file = mentions_dir / "2026-07-18.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text(encoding="utf-8")) == mentions
