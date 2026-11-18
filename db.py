"""SQLite veri katmanı. Streamlit'e bağımlı değil, böylece test edilebilir."""

import sqlite3
from datetime import datetime, timezone

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY,
    day INTEGER,
    task TEXT,
    completed INTEGER DEFAULT 0,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_notes (
    day INTEGER PRIMARY KEY,
    small_win TEXT,
    energy_morning INTEGER,
    energy_noon INTEGER,
    energy_evening INTEGER,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_entries (
    day TEXT PRIMARY KEY,
    sleep_start TEXT,
    sleep_end TEXT,
    sleep_quality INTEGER,
    sleep_notes TEXT,
    morning_routine INTEGER,
    evening_routine INTEGER,
    mini_goals TEXT,
    reflection TEXT,
    gratitude TEXT,
    intention TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS weekly_reflections (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    draining TEXT,
    strengthening TEXT,
    learned TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: str, days: int, task_names: list[str]) -> sqlite3.Connection:
    """Bağlantıyı açar, şemayı kurar ve eksik gün/görev satırlarını ekler.

    Var olan satırlara dokunmaz, yani config.py'ye yeni görev eklemek
    eski verileri bozmaz.
    """
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript(SCHEMA)
    existing = set(conn.execute("SELECT day, task FROM progress").fetchall())
    missing = [
        (d, t, _now())
        for d in range(1, days + 1)
        for t in task_names
        if (d, t) not in existing
    ]
    if missing:
        conn.executemany(
            "INSERT INTO progress (day, task, completed, updated_at) VALUES (?, ?, 0, ?)",
            missing,
        )
    conn.commit()
    return conn


# --- Görevler ---
def get_progress(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT day, task, completed, updated_at FROM progress ORDER BY day, task", conn
    )


def set_completed(conn, day: int, task: str, done: bool) -> None:
    conn.execute(
        "UPDATE progress SET completed = ?, updated_at = ? WHERE day = ? AND task = ?",
        (int(done), _now(), day, task),
    )
    conn.commit()


def reset_all(conn) -> None:
    conn.execute("UPDATE progress SET completed = 0, updated_at = ?", (_now(),))
    conn.execute("DELETE FROM daily_notes")
    conn.commit()


# --- Günlük notlar ---
def get_daily_notes(conn, day: int) -> dict:
    df = pd.read_sql_query("SELECT * FROM daily_notes WHERE day = ?", conn, params=(day,))
    return df.iloc[0].to_dict() if not df.empty else {}


def get_all_notes(conn) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM daily_notes ORDER BY day", conn)


def save_daily_notes(conn, day, small_win, morning, noon, evening) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO daily_notes
           (day, small_win, energy_morning, energy_noon, energy_evening, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (day, small_win, morning, noon, evening, _now()),
    )
    conn.commit()


# --- Detaylı günlük ---
ENTRY_FIELDS = [
    "sleep_start", "sleep_end", "sleep_quality", "sleep_notes",
    "morning_routine", "evening_routine", "mini_goals",
    "reflection", "gratitude", "intention",
]


def get_daily_entry(conn, day_iso: str) -> dict:
    df = pd.read_sql_query(
        "SELECT * FROM daily_entries WHERE day = ?", conn, params=(day_iso,)
    )
    return df.iloc[0].to_dict() if not df.empty else {}


def save_daily_entry(conn, day_iso: str, **fields) -> None:
    values = [fields.get(f) for f in ENTRY_FIELDS]
    conn.execute(
        f"""INSERT OR REPLACE INTO daily_entries
            (day, {", ".join(ENTRY_FIELDS)}, updated_at)
            VALUES ({", ".join("?" * (len(ENTRY_FIELDS) + 2))})""",
        (day_iso, *values, _now()),
    )
    conn.commit()


def get_all_entries(conn) -> pd.DataFrame:
    df = pd.read_sql_query("SELECT * FROM daily_entries ORDER BY day", conn)
    if not df.empty:
        df["sleep_hours"] = [
            sleep_hours(s, e) for s, e in zip(df["sleep_start"], df["sleep_end"])
        ]
    return df


def sleep_hours(start: str, end: str) -> float:
    """Uyku süresini saat olarak döner; gece yarısını geçen uykuyu doğru hesaplar.

    22:00 -> 06:00 = 8 saat (eski sürüm bunu -16 saat buluyordu).
    """
    def minutes(t: str) -> int:
        parts = [int(p) for p in str(t).split(":")[:2]]
        return parts[0] * 60 + parts[1]

    diff = minutes(end) - minutes(start)
    if diff < 0:
        diff += 24 * 60
    return round(diff / 60, 2)


# --- Haftalık refleksiyon ---
def save_weekly_reflection(conn, draining, strengthening, learned) -> None:
    conn.execute(
        """INSERT INTO weekly_reflections (created_at, draining, strengthening, learned)
           VALUES (?, ?, ?, ?)""",
        (_now(), draining, strengthening, learned),
    )
    conn.commit()


def get_weekly_reflections(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT created_at, draining, strengthening, learned "
        "FROM weekly_reflections ORDER BY created_at DESC",
        conn,
    )
