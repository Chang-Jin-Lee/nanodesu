# tests/test_build_events.py
import json
from datetime import date

from scripts.build_events import (
    load_latest_collabocafe_events,
    load_conventions,
    dedupe_events,
    drop_past_events,
    sort_events,
    build_events,
    run,
)

SAMPLE_COLLABOCAFE_EVENTS = [
    {"title": "Cafe A", "url": "u1", "venue": "Shibuya", "start_date": "2026-07-20", "end_date": "2026-08-01", "category": "cafe", "description": "", "source_site": "collabocafe"},
    {"title": "Cafe B", "url": "u2", "venue": "Ikebukuro", "start_date": "2026-06-01", "end_date": "2026-06-10", "category": "cafe", "description": "", "source_site": "collabocafe"},
]


def test_load_latest_collabocafe_events_reads_most_recent_file(tmp_path):
    raw_dir = tmp_path / "collabocafe"
    raw_dir.mkdir()
    (raw_dir / "2026-07-16.json").write_text(json.dumps([{"title": "Old"}]), encoding="utf-8")
    (raw_dir / "2026-07-18.json").write_text(json.dumps(SAMPLE_COLLABOCAFE_EVENTS), encoding="utf-8")
    events = load_latest_collabocafe_events(raw_dir=raw_dir)
    assert events == SAMPLE_COLLABOCAFE_EVENTS


def test_load_latest_collabocafe_events_returns_empty_when_no_files(tmp_path):
    assert load_latest_collabocafe_events(raw_dir=tmp_path / "missing") == []


def test_load_conventions_reads_yaml(tmp_path):
    path = tmp_path / "conventions.yaml"
    path.write_text(
        "conventions:\n  - title: \"Test Con\"\n    venue: \"Tokyo\"\n    start_date: \"2026-08-01\"\n    end_date: \"2026-08-02\"\n    url: \"https://example.com\"\n",
        encoding="utf-8",
    )
    conventions = load_conventions(path)
    assert conventions == [
        {"title": "Test Con", "venue": "Tokyo", "start_date": "2026-08-01", "end_date": "2026-08-02", "url": "https://example.com", "source_site": "conventions.yaml"}
    ]


def test_dedupe_events_removes_exact_title_venue_start_duplicates():
    events = SAMPLE_COLLABOCAFE_EVENTS + [SAMPLE_COLLABOCAFE_EVENTS[0]]
    assert len(dedupe_events(events)) == 2


def test_drop_past_events_removes_events_whose_end_date_has_passed():
    kept = drop_past_events(SAMPLE_COLLABOCAFE_EVENTS, today=date(2026, 7, 18))
    titles = {e["title"] for e in kept}
    assert titles == {"Cafe A"}


def test_drop_past_events_keeps_events_with_no_end_date():
    events = [{"title": "Ongoing", "end_date": None}]
    assert drop_past_events(events, today=date(2026, 7, 18)) == events


def test_sort_events_orders_by_start_date_ascending_nulls_last():
    events = [
        {"title": "Later", "start_date": "2026-09-01"},
        {"title": "No date", "start_date": None},
        {"title": "Sooner", "start_date": "2026-07-20"},
    ]
    ordered = [e["title"] for e in sort_events(events)]
    assert ordered == ["Sooner", "Later", "No date"]


def test_build_events_combines_dedupes_drops_past_and_sorts():
    convention_events = [
        {"title": "Comiket", "venue": "Tokyo", "start_date": "2026-06-01", "end_date": "2026-06-02", "url": "u", "source_site": "conventions.yaml"},
    ]
    result = build_events(SAMPLE_COLLABOCAFE_EVENTS, convention_events, today=date(2026, 7, 18))
    titles = [e["title"] for e in result]
    assert titles == ["Cafe A"]


def test_run_writes_japan_events_json(tmp_path):
    raw_dir = tmp_path / "data" / "events" / "collabocafe"
    raw_dir.mkdir(parents=True)
    (raw_dir / "2026-07-18.json").write_text(json.dumps(SAMPLE_COLLABOCAFE_EVENTS), encoding="utf-8")
    conventions_path = tmp_path / "conventions.yaml"
    conventions_path.write_text("conventions: []\n", encoding="utf-8")
    out_path = tmp_path / "data" / "events" / "japan-events.json"

    run(
        today=date(2026, 7, 18),
        raw_dir=raw_dir,
        conventions_path=conventions_path,
        out_path=out_path,
    )

    assert out_path.exists()
    assert json.loads(out_path.read_text(encoding="utf-8")) == [
        {"title": "Cafe A", "url": "u1", "venue": "Shibuya", "start_date": "2026-07-20", "end_date": "2026-08-01", "category": "cafe", "description": "", "source_site": "collabocafe"},
    ]
