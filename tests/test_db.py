import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import db  # noqa: E402

TASKS = ["Uyku", "Hareket"]


@pytest.fixture
def conn():
    c = db.connect(":memory:", 3, TASKS)
    yield c
    c.close()


def test_connect_seeds_every_day_and_task(conn):
    df = db.get_progress(conn)
    assert len(df) == 3 * len(TASKS)
    assert df["completed"].sum() == 0


def test_new_task_in_config_is_backfilled(tmp_path):
    path = str(tmp_path / "t.db")
    c = db.connect(path, 2, ["A"])
    db.set_completed(c, 1, "A", True)
    c.close()
    c = db.connect(path, 2, ["A", "B"])
    df = db.get_progress(c)
    assert len(df) == 4
    assert df[(df.day == 1) & (df.task == "A")]["completed"].iloc[0] == 1


def test_set_completed_and_reset(conn):
    db.set_completed(conn, 2, "Hareket", True)
    db.save_daily_notes(conn, 2, "win", 3, 4, 5)
    assert db.get_progress(conn)["completed"].sum() == 1
    db.reset_all(conn)
    assert db.get_progress(conn)["completed"].sum() == 0
    assert db.get_daily_notes(conn, 2) == {}


def test_daily_notes_roundtrip(conn):
    db.save_daily_notes(conn, 1, "yürüdüm", 2, 3, 4)
    notes = db.get_daily_notes(conn, 1)
    assert notes["small_win"] == "yürüdüm"
    assert notes["energy_evening"] == 4


def test_quotes_in_input_are_safe(conn):
    tricky = "x'; DROP TABLE daily_entries; --"
    db.save_daily_entry(conn, tricky, sleep_start="23:00:00", sleep_end="07:00:00")
    assert db.get_daily_entry(conn, tricky)["sleep_start"] == "23:00:00"


@pytest.mark.parametrize(
    "start,end,hours",
    [("22:00:00", "06:00:00", 8.0), ("00:30", "08:00", 7.5), ("23:45:00", "23:45:00", 0.0)],
)
def test_sleep_hours_crosses_midnight(start, end, hours):
    assert db.sleep_hours(start, end) == hours


def test_entries_include_sleep_hours(conn):
    db.save_daily_entry(conn, "2026-01-01", sleep_start="23:00:00", sleep_end="07:00:00")
    assert db.get_all_entries(conn)["sleep_hours"].iloc[0] == 8.0


def test_weekly_reflection_stored_in_db(conn):
    db.save_weekly_reflection(conn, "yorgunluk", "yürüyüş", "sabır")
    df = db.get_weekly_reflections(conn)
    assert df.iloc[0]["learned"] == "sabır"
