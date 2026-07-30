import json
from datetime import date

from scripts.rank_trends import (
    load_mentions_in_window,
    rank_mentions,
    build_trend_report,
    load_all_mentions,
    run,
    load_previous_ranks,
    attach_deltas,
)

SAMPLE_MENTIONS = [
    {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "u1"},
    {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-12", "source": "gematsu", "item_url": "u2"},
    {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-06-01", "source": "ann", "item_url": "u3"},
    {"watch_title": "Haikyu!!", "category": "anime", "region": "global", "date": "2026-07-17", "source": "ann", "item_url": "u4"},
    {"watch_title": "Genshin Impact", "category": "game", "region": "global", "date": "2026-07-17", "source": "gematsu", "item_url": "u6"},
    {"watch_title": "Umamusume: Pretty Derby", "category": "game", "region": "japan", "date": "2026-07-17", "source": "4gamer", "item_url": "u5"},
    {"watch_title": "ONE PIECE", "category": "manga", "region": "japan", "date": "2026-07-17", "source": "shonenjump", "item_url": "u7"},
]


def test_load_mentions_in_window_filters_by_trailing_days():
    reference = date(2026, 7, 18)
    windowed = load_mentions_in_window(SAMPLE_MENTIONS, reference, window_days=7)
    dates = {m["date"] for m in windowed}
    assert dates == {"2026-07-18", "2026-07-12", "2026-07-17"}
    assert "2026-06-01" not in dates


def test_load_mentions_in_window_ignores_entries_missing_date():
    mentions = SAMPLE_MENTIONS + [{"watch_title": "X", "region": "global", "date": "", "source": "y", "item_url": "z"}]
    windowed = load_mentions_in_window(mentions, date(2026, 7, 18), window_days=30)
    assert all(m["date"] for m in windowed)


def test_rank_mentions_counts_and_sorts_descending_within_region_and_category():
    ranked = rank_mentions(SAMPLE_MENTIONS, region="global", category="anime")
    assert ranked[0]["title"] == "ONE PIECE"
    assert ranked[0]["mentions"] == 3
    assert set(ranked[0]["sources"]) == {"ann", "gematsu"}
    assert ranked[1]["title"] == "Haikyu!!"
    titles = {e["title"] for e in ranked}
    assert "Genshin Impact" not in titles
    assert "Umamusume: Pretty Derby" not in titles


def test_rank_mentions_filters_by_category_within_region():
    ranked = rank_mentions(SAMPLE_MENTIONS, region="global", category="game")
    assert [e["title"] for e in ranked] == ["Genshin Impact"]


def test_rank_mentions_filters_manga_category_within_region():
    ranked = rank_mentions(SAMPLE_MENTIONS, region="japan", category="manga")
    assert [e["title"] for e in ranked] == ["ONE PIECE"]
    assert ranked[0]["sources"] == ["shonenjump"]


def test_rank_mentions_treats_missing_category_as_anime():
    mentions = [
        {"watch_title": "Old Record", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "u1"},
    ]
    assert rank_mentions(mentions, region="global", category="anime")[0]["title"] == "Old Record"
    assert rank_mentions(mentions, region="global", category="game") == []


def test_rank_mentions_dedupes_same_item_url_across_runs():
    mentions = [
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-14", "source": "ann", "item_url": "https://ann/1"},
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-16", "source": "ann", "item_url": "https://ann/1"},
    ]
    ranked = rank_mentions(mentions, region="global", category="anime")
    assert len(ranked) == 1
    assert ranked[0]["mentions"] == 1


def test_rank_mentions_counts_distinct_item_urls_separately():
    mentions = [
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-14", "source": "ann", "item_url": "https://ann/1"},
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-16", "source": "ann", "item_url": "https://ann/2"},
    ]
    ranked = rank_mentions(mentions, region="global", category="anime")
    assert len(ranked) == 1
    assert ranked[0]["mentions"] == 2


def test_rank_mentions_does_not_collapse_missing_item_urls():
    mentions = [
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-14", "source": "ann", "item_url": ""},
        {"watch_title": "ONE PIECE", "category": "anime", "region": "global", "date": "2026-07-16", "source": "gematsu", "item_url": ""},
    ]
    ranked = rank_mentions(mentions, region="global", category="anime")
    assert len(ranked) == 1
    assert ranked[0]["mentions"] == 2


def test_build_trend_report_combines_window_and_rank(tmp_path):
    report = build_trend_report(SAMPLE_MENTIONS, region="global", category="anime", window_days=7, reference_date=date(2026, 7, 18))
    assert report["region"] == "global"
    assert report["category"] == "anime"
    assert report["window_days"] == 7
    titles = [e["title"] for e in report["entries"]]
    assert "ONE PIECE" in titles
    assert "Genshin Impact" not in titles
    assert "generated_at" in report


def test_load_all_mentions_reads_every_mentions_file(tmp_path):
    mentions_dir = tmp_path / "mentions"
    mentions_dir.mkdir()
    (mentions_dir / "2026-07-17.json").write_text(json.dumps(SAMPLE_MENTIONS[:2]), encoding="utf-8")
    (mentions_dir / "2026-07-18.json").write_text(json.dumps(SAMPLE_MENTIONS[2:]), encoding="utf-8")
    all_mentions = load_all_mentions(mentions_dir)
    assert len(all_mentions) == len(SAMPLE_MENTIONS)


def test_run_writes_twelve_trend_files(tmp_path):
    mentions_dir = tmp_path / "mentions"
    mentions_dir.mkdir()
    (mentions_dir / "2026-07-18.json").write_text(json.dumps(SAMPLE_MENTIONS), encoding="utf-8")
    out_dir = tmp_path / "trends"

    run(reference_date=date(2026, 7, 18), mentions_dir=mentions_dir, out_dir=out_dir)

    expected = [
        f"{region}-{category}-{window}d.json"
        for region in ("global", "japan")
        for category in ("anime", "manga", "game")
        for window in (7, 30)
    ]
    assert len(expected) == 12
    for name in expected:
        assert (out_dir / name).exists(), f"missing {name}"
    global_anime_7d = json.loads((out_dir / "global-anime-7d.json").read_text(encoding="utf-8"))
    assert global_anime_7d["entries"][0]["title"] == "ONE PIECE"
    global_game_7d = json.loads((out_dir / "global-game-7d.json").read_text(encoding="utf-8"))
    assert [e["title"] for e in global_game_7d["entries"]] == ["Genshin Impact"]
    japan_manga_7d = json.loads((out_dir / "japan-manga-7d.json").read_text(encoding="utf-8"))
    assert [e["title"] for e in japan_manga_7d["entries"]] == ["ONE PIECE"]


def test_load_previous_ranks_reads_existing_trend_file(tmp_path):
    path = tmp_path / "global-7d.json"
    path.write_text(
        json.dumps({"entries": [{"title": "A", "mentions": 5, "sources": []}, {"title": "B", "mentions": 3, "sources": []}]}),
        encoding="utf-8",
    )
    assert load_previous_ranks(path) == {"A": 1, "B": 2}


def test_load_previous_ranks_returns_empty_dict_when_file_absent(tmp_path):
    assert load_previous_ranks(tmp_path / "missing.json") == {}


def test_run_reads_previous_ranks_before_overwriting_out_file(tmp_path):
    """Regression test: run() must call load_previous_ranks(out_path) BEFORE
    it writes the newly computed report to out_path. If a future refactor
    reordered this to read-after-write, every entry would be compared
    against itself and every delta would silently become 0. Two runs against
    the same out_dir, with the ranking flipped between them, catch that:
    if the bug were present neither title's delta would move.
    """
    out_dir = tmp_path / "trends"

    first_mentions_dir = tmp_path / "mentions_first"
    first_mentions_dir.mkdir()
    first_mentions = [
        {"watch_title": "A", "category": "anime", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "a1"},
        {"watch_title": "A", "category": "anime", "region": "global", "date": "2026-07-17", "source": "ann", "item_url": "a2"},
        {"watch_title": "A", "category": "anime", "region": "global", "date": "2026-07-16", "source": "ann", "item_url": "a3"},
        {"watch_title": "B", "category": "anime", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "b1"},
    ]
    (first_mentions_dir / "2026-07-18.json").write_text(json.dumps(first_mentions), encoding="utf-8")

    run(reference_date=date(2026, 7, 18), mentions_dir=first_mentions_dir, out_dir=out_dir)

    first_global_anime_7d = json.loads((out_dir / "global-anime-7d.json").read_text(encoding="utf-8"))
    assert first_global_anime_7d["entries"][0]["title"] == "A"
    assert first_global_anime_7d["entries"][1]["title"] == "B"

    second_mentions_dir = tmp_path / "mentions_second"
    second_mentions_dir.mkdir()
    second_mentions = [
        {"watch_title": "B", "category": "anime", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "b1"},
        {"watch_title": "B", "category": "anime", "region": "global", "date": "2026-07-17", "source": "ann", "item_url": "b2"},
        {"watch_title": "B", "category": "anime", "region": "global", "date": "2026-07-16", "source": "ann", "item_url": "b3"},
        {"watch_title": "A", "category": "anime", "region": "global", "date": "2026-07-18", "source": "ann", "item_url": "a1"},
    ]
    (second_mentions_dir / "2026-07-18.json").write_text(json.dumps(second_mentions), encoding="utf-8")

    run(reference_date=date(2026, 7, 18), mentions_dir=second_mentions_dir, out_dir=out_dir)

    second_global_anime_7d = json.loads((out_dir / "global-anime-7d.json").read_text(encoding="utf-8"))
    entries_by_title = {e["title"]: e for e in second_global_anime_7d["entries"]}

    assert entries_by_title["B"]["mentions"] == 3
    assert entries_by_title["A"]["mentions"] == 1
    assert second_global_anime_7d["entries"][0]["title"] == "B"
    assert second_global_anime_7d["entries"][1]["title"] == "A"

    assert entries_by_title["B"]["delta"] == 1
    assert entries_by_title["A"]["delta"] == -1


def test_attach_deltas_marks_risen_fallen_unchanged_and_new():
    entries = [{"title": "B", "mentions": 9, "sources": []}, {"title": "A", "mentions": 5, "sources": []}, {"title": "C", "mentions": 1, "sources": []}]
    previous_ranks = {"A": 1, "B": 2}
    result = attach_deltas(entries, previous_ranks)
    assert result[0]["delta"] == 1
    assert result[1]["delta"] == -1
    assert result[2]["delta"] is None
