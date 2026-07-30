# tests/test_sync_watchlist.py
import json
import yaml

from scripts.sync_watchlist import (
    load_watchlist_data,
    flatten_known_names,
    build_aliases,
    find_new_entries,
    add_entries_to_watchlist,
    enrich_empty_aliases,
    load_latest_anilist_entries,
    run,
)

SAMPLE_WATCHLIST = {
    "titles": [
        {"canonical": "ONE PIECE", "aliases": ["ワンピース", "One Piece"]},
        {"canonical": "Haikyu!!", "aliases": ["ハイキュー"]},
    ]
}


def test_flatten_known_names_includes_canonical_and_aliases_lowercased():
    known = flatten_known_names(SAMPLE_WATCHLIST)
    assert "one piece" in known
    assert "ワンピース" in known
    assert "haikyu!!" in known
    assert "ハイキュー" in known


def test_find_new_entries_excludes_already_known_case_insensitive():
    anilist_entries = [
        {"title": "one piece"},
        {"title": "Frieren: Beyond Journey's End"},
    ]
    new_entries = find_new_entries(anilist_entries, SAMPLE_WATCHLIST)
    assert [e["title"] for e in new_entries] == ["Frieren: Beyond Journey's End"]


def test_find_new_entries_dedupes_within_same_anilist_batch():
    anilist_entries = [
        {"title": "Frieren: Beyond Journey's End"},
        {"title": "frieren: beyond journey's end"},
    ]
    new_entries = find_new_entries(anilist_entries, SAMPLE_WATCHLIST)
    assert [e["title"] for e in new_entries] == ["Frieren: Beyond Journey's End"]


def test_find_new_entries_skips_blank_titles():
    anilist_entries = [{"title": ""}, {"title": "  "}]
    assert find_new_entries(anilist_entries, SAMPLE_WATCHLIST) == []


def test_build_aliases_collects_native_and_romaji():
    entry = {"title": "Frieren", "native_title": "葬送のフリーレン", "romaji_title": "Sousou no Frieren"}
    assert build_aliases(entry) == ["葬送のフリーレン", "Sousou no Frieren"]


def test_build_aliases_drops_alias_equal_to_canonical_case_insensitively():
    entry = {"title": "ONE PIECE", "native_title": "ONE PIECE", "romaji_title": "one piece"}
    assert build_aliases(entry) == []


def test_build_aliases_drops_blank_and_missing_values():
    assert build_aliases({"title": "Solo", "native_title": "", "romaji_title": None}) == []
    assert build_aliases({"title": "Solo"}) == []


def test_add_entries_to_watchlist_appends_with_category_and_aliases():
    entry = {"title": "New Show", "native_title": "新番組", "romaji_title": "Shin Bangumi"}
    updated = add_entries_to_watchlist(SAMPLE_WATCHLIST, [entry], "manga")
    assert updated["titles"][-1] == {
        "canonical": "New Show",
        "category": "manga",
        "aliases": ["新番組", "Shin Bangumi"],
    }
    assert len(updated["titles"]) == 3
    assert updated["titles"][0] == SAMPLE_WATCHLIST["titles"][0]


def test_enrich_empty_aliases_fills_in_native_for_existing_entry():
    watchlist = {"titles": [{"canonical": "Bleach", "category": "anime", "aliases": []}]}
    entries = [{"title": "Bleach", "native_title": "ブリーチ", "romaji_title": "Bleach"}]
    updated, changed = enrich_empty_aliases(watchlist, entries)
    assert changed is True
    assert updated["titles"][0]["aliases"] == ["ブリーチ"]
    assert updated["titles"][0]["category"] == "anime"


def test_enrich_empty_aliases_leaves_populated_aliases_untouched():
    watchlist = {"titles": [{"canonical": "ONE PIECE", "aliases": ["ワンピース"]}]}
    entries = [{"title": "ONE PIECE", "native_title": "ONE PIECE (native)", "romaji_title": "ONE PIECE"}]
    updated, changed = enrich_empty_aliases(watchlist, entries)
    assert changed is False
    assert updated["titles"][0]["aliases"] == ["ワンピース"]


def test_enrich_empty_aliases_reports_no_change_when_nothing_to_add():
    watchlist = {"titles": [{"canonical": "Bleach", "aliases": []}]}
    entries = [{"title": "Bleach", "native_title": "", "romaji_title": "Bleach"}]
    updated, changed = enrich_empty_aliases(watchlist, entries)
    assert changed is False
    assert updated["titles"][0]["aliases"] == []


def test_load_latest_anilist_entries_reads_most_recent_file(tmp_path):
    raw_dir = tmp_path / "anilist"
    raw_dir.mkdir()
    (raw_dir / "2026-07-16.json").write_text(json.dumps([{"title": "Old"}]), encoding="utf-8")
    (raw_dir / "2026-07-18.json").write_text(json.dumps([{"title": "New"}]), encoding="utf-8")
    entries = load_latest_anilist_entries(raw_dir=raw_dir)
    assert entries == [{"title": "New"}]


def test_load_latest_anilist_entries_returns_empty_when_no_files(tmp_path):
    assert load_latest_anilist_entries(raw_dir=tmp_path / "missing") == []


def _write_raw(raw_dir, entries):
    raw_dir.mkdir(parents=True)
    (raw_dir / "2026-07-18.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


def test_run_adds_anime_and_manga_with_their_categories(tmp_path):
    anime_dir = tmp_path / "anilist"
    manga_dir = tmp_path / "anilist-manga"
    _write_raw(anime_dir, [
        {"title": "ONE PIECE", "native_title": "ONE PIECE", "romaji_title": "ONE PIECE"},
        {"title": "Frieren: Beyond Journey's End", "native_title": "葬送のフリーレン", "romaji_title": "Sousou no Frieren"},
    ])
    _write_raw(manga_dir, [
        {"title": "Kagurabachi", "native_title": "カグラバチ", "romaji_title": "Kagurabachi"},
    ])
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(yaml.safe_dump(SAMPLE_WATCHLIST, allow_unicode=True), encoding="utf-8")

    added = run(anilist_raw_dir=anime_dir, anilist_manga_raw_dir=manga_dir, watchlist_path=watchlist_path)

    assert added == ["Frieren: Beyond Journey's End", "Kagurabachi"]
    updated = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    by_canonical = {e["canonical"]: e for e in updated["titles"]}
    assert by_canonical["Frieren: Beyond Journey's End"]["category"] == "anime"
    assert by_canonical["Frieren: Beyond Journey's End"]["aliases"] == ["葬送のフリーレン", "Sousou no Frieren"]
    assert by_canonical["Kagurabachi"]["category"] == "manga"
    assert by_canonical["Kagurabachi"]["aliases"] == ["カグラバチ"]


def test_run_registers_a_dual_trending_title_once_as_anime(tmp_path):
    anime_dir = tmp_path / "anilist"
    manga_dir = tmp_path / "anilist-manga"
    dual = {"title": "Kagurabachi", "native_title": "カグラバチ", "romaji_title": "Kagurabachi"}
    _write_raw(anime_dir, [dual])
    _write_raw(manga_dir, [dual])
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(yaml.safe_dump(SAMPLE_WATCHLIST, allow_unicode=True), encoding="utf-8")

    added = run(anilist_raw_dir=anime_dir, anilist_manga_raw_dir=manga_dir, watchlist_path=watchlist_path)

    assert added == ["Kagurabachi"]
    updated = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    canonicals = [e["canonical"] for e in updated["titles"]]
    assert canonicals.count("Kagurabachi") == 1
    by_canonical = {e["canonical"]: e for e in updated["titles"]}
    assert by_canonical["Kagurabachi"]["category"] == "anime"


def test_run_enriches_existing_entry_with_empty_aliases(tmp_path):
    anime_dir = tmp_path / "anilist"
    manga_dir = tmp_path / "anilist-manga"
    _write_raw(anime_dir, [{"title": "Bleach", "native_title": "ブリーチ", "romaji_title": "Bleach"}])
    _write_raw(manga_dir, [])
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(
        yaml.safe_dump({"titles": [{"canonical": "Bleach", "category": "anime", "aliases": []}]}, allow_unicode=True),
        encoding="utf-8",
    )

    added = run(anilist_raw_dir=anime_dir, anilist_manga_raw_dir=manga_dir, watchlist_path=watchlist_path)

    assert added == []
    updated = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    assert updated["titles"][0]["aliases"] == ["ブリーチ"]


def test_run_does_not_rewrite_file_when_nothing_new(tmp_path):
    anime_dir = tmp_path / "anilist"
    manga_dir = tmp_path / "anilist-manga"
    _write_raw(anime_dir, [{"title": "ONE PIECE", "native_title": "ワンピース", "romaji_title": "ONE PIECE"}])
    _write_raw(manga_dir, [])
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(yaml.safe_dump(SAMPLE_WATCHLIST, allow_unicode=True), encoding="utf-8")
    before_mtime = watchlist_path.stat().st_mtime_ns

    added = run(anilist_raw_dir=anime_dir, anilist_manga_raw_dir=manga_dir, watchlist_path=watchlist_path)

    assert added == []
    assert watchlist_path.stat().st_mtime_ns == before_mtime
