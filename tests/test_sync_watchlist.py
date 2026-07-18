# tests/test_sync_watchlist.py
import json
import yaml

from scripts.sync_watchlist import (
    load_watchlist_data,
    flatten_known_names,
    find_new_titles,
    add_titles_to_watchlist,
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


def test_find_new_titles_excludes_already_known_case_insensitive():
    anilist_entries = [
        {"title": "one piece"},
        {"title": "Frieren: Beyond Journey's End"},
    ]
    new_titles = find_new_titles(anilist_entries, SAMPLE_WATCHLIST)
    assert new_titles == ["Frieren: Beyond Journey's End"]


def test_find_new_titles_dedupes_within_same_anilist_batch():
    anilist_entries = [
        {"title": "Frieren: Beyond Journey's End"},
        {"title": "frieren: beyond journey's end"},
    ]
    new_titles = find_new_titles(anilist_entries, SAMPLE_WATCHLIST)
    assert new_titles == ["Frieren: Beyond Journey's End"]


def test_find_new_titles_skips_blank_titles():
    anilist_entries = [{"title": ""}, {"title": "  "}]
    assert find_new_titles(anilist_entries, SAMPLE_WATCHLIST) == []


def test_add_titles_to_watchlist_appends_new_entries_with_anime_category():
    updated = add_titles_to_watchlist(SAMPLE_WATCHLIST, ["New Show"])
    assert updated["titles"][-1] == {"canonical": "New Show", "category": "anime", "aliases": []}
    assert len(updated["titles"]) == 3
    assert updated["titles"][0] == SAMPLE_WATCHLIST["titles"][0]


def test_load_latest_anilist_entries_reads_most_recent_file(tmp_path):
    raw_dir = tmp_path / "anilist"
    raw_dir.mkdir()
    (raw_dir / "2026-07-16.json").write_text(json.dumps([{"title": "Old"}]), encoding="utf-8")
    (raw_dir / "2026-07-18.json").write_text(json.dumps([{"title": "New"}]), encoding="utf-8")
    entries = load_latest_anilist_entries(raw_dir=raw_dir)
    assert entries == [{"title": "New"}]


def test_load_latest_anilist_entries_returns_empty_when_no_files(tmp_path):
    assert load_latest_anilist_entries(raw_dir=tmp_path / "missing") == []


def test_run_writes_updated_watchlist_and_returns_new_titles(tmp_path):
    raw_dir = tmp_path / "anilist"
    raw_dir.mkdir()
    (raw_dir / "2026-07-18.json").write_text(
        json.dumps([{"title": "ONE PIECE"}, {"title": "Frieren: Beyond Journey's End"}]),
        encoding="utf-8",
    )
    watchlist_path = tmp_path / "watchlist.yaml"
    watchlist_path.write_text(yaml.safe_dump(SAMPLE_WATCHLIST, allow_unicode=True), encoding="utf-8")

    added = run(anilist_raw_dir=raw_dir, watchlist_path=watchlist_path)

    assert added == ["Frieren: Beyond Journey's End"]
    updated = yaml.safe_load(watchlist_path.read_text(encoding="utf-8"))
    canonicals = [e["canonical"] for e in updated["titles"]]
    assert "Frieren: Beyond Journey's End" in canonicals
    assert "ONE PIECE" in canonicals
    by_canonical = {e["canonical"]: e for e in updated["titles"]}
    assert by_canonical["Frieren: Beyond Journey's End"]["category"] == "anime"


def test_run_does_not_rewrite_file_when_nothing_new(tmp_path):
    raw_dir = tmp_path / "anilist"
    raw_dir.mkdir()
    (raw_dir / "2026-07-18.json").write_text(json.dumps([{"title": "ONE PIECE"}]), encoding="utf-8")
    watchlist_path = tmp_path / "watchlist.yaml"
    original_text = yaml.safe_dump(SAMPLE_WATCHLIST, allow_unicode=True)
    watchlist_path.write_text(original_text, encoding="utf-8")
    before_mtime = watchlist_path.stat().st_mtime_ns

    added = run(anilist_raw_dir=raw_dir, watchlist_path=watchlist_path)

    assert added == []
    assert watchlist_path.stat().st_mtime_ns == before_mtime
