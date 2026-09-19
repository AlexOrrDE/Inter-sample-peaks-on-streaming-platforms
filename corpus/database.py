import sqlite3
import pandas as pd

from datetime import datetime, timezone
from pathlib import Path

schema = """
CREATE TABLE IF NOT EXISTS tracks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,

    platform         TEXT    NOT NULL,
    codec            TEXT    NOT NULL,
    bitrate_kbps     INTEGER,
    quality_label    TEXT,
    normalisation    TEXT,

    title            TEXT    NOT NULL,
    artist           TEXT    NOT NULL,
    album            TEXT,
    release_year     INTEGER,
    genre            TEXT,
    duration_ms      INTEGER,
    platform_id      TEXT,

    sample_peak_dbfs REAL,
    true_peak_dbtp   REAL,
    isp_margin_db    REAL,
    has_isp          INTEGER NOT NULL,
    n_isp_events     INTEGER,
    isp_events_per_min REAL,
    n_isp_samples    INTEGER,
    isp_over_fraction REAL,
    isp_over_pct     REAL,
    integrated_lufs  REAL,

    captured_at      TEXT    NOT NULL
);
"""


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    statements = schema.split(";")
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)

    conn.commit()
    return conn


def insert(conn, record):
    if "captured_at" in record:
        record = dict(record)
    else:
        record = dict(record)
        record["captured_at"] = datetime.now(timezone.utc).isoformat()
    cols = ", ".join(record.keys())
    placeholders = ", ".join("?" * len(record))
    cur = conn.execute(
        f"INSERT INTO tracks ({cols}) VALUES ({placeholders})",
        list(record.values()),
    )
    conn.commit()
    return cur.lastrowid


def get(conn, row_id):
    cur = conn.execute("SELECT * FROM tracks WHERE id = ?", (row_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def exists(conn, platform, platform_id, normalisation):
    cur = conn.execute(
        "SELECT 1 FROM tracks WHERE platform = ? AND platform_id = ? AND normalisation = ?",
        (platform, platform_id, normalisation),
    )
    return cur.fetchone() is not None


def count(conn):
    return conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]


def to_df(conn):
    df = pd.read_sql("SELECT * FROM tracks", conn)
    return df
