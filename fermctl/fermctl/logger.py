"""SQLite logger for fermentation data.

Stores fermentation runs and temperature readings. Uses WAL mode
for safe concurrent access from the controller thread and the API.
"""

import os
import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger("fermctl.logger")


class FermLogger:
    """Manages the fermentation database."""

    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS fermentation_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id   INTEGER,
                recipe_name TEXT DEFAULT '',
                profile     TEXT DEFAULT '[]',
                started_at  TEXT NOT NULL,
                ended_at    TEXT,
                active      INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS temperature_readings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      INTEGER NOT NULL REFERENCES fermentation_runs(id),
                timestamp   TEXT NOT NULL,
                temp_f      REAL NOT NULL,
                target_f    REAL NOT NULL,
                heat_on     INTEGER NOT NULL DEFAULT 0,
                cool_on     INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_readings_run_ts
                ON temperature_readings(run_id, timestamp);
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized at %s", self.db_path)

    def start_run(self, recipe_id=None, recipe_name="", profile_json="[]"):
        """Create a new fermentation run. Returns the run ID."""
        conn = self._connect()
        cur = conn.execute(
            "INSERT INTO fermentation_runs (recipe_id, recipe_name, profile, started_at) "
            "VALUES (?, ?, ?, ?)",
            (recipe_id, recipe_name, profile_json, _now()),
        )
        run_id = cur.lastrowid
        conn.commit()
        conn.close()
        logger.info("Created run #%d", run_id)
        return run_id

    def end_run(self, run_id):
        """Mark a fermentation run as ended."""
        conn = self._connect()
        conn.execute(
            "UPDATE fermentation_runs SET ended_at = ?, active = 0 WHERE id = ?",
            (_now(), run_id),
        )
        conn.commit()
        conn.close()

    def update_run_profile(self, run_id, profile_json):
        """Update the profile on an active run."""
        conn = self._connect()
        conn.execute(
            "UPDATE fermentation_runs SET profile = ? WHERE id = ?",
            (profile_json, run_id),
        )
        conn.commit()
        conn.close()

    def log_reading(self, run_id, temp_f, target_f, heat_on, cool_on):
        """Log a single temperature reading."""
        conn = self._connect()
        conn.execute(
            "INSERT INTO temperature_readings "
            "(run_id, timestamp, temp_f, target_f, heat_on, cool_on) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, _now(), temp_f, target_f, int(heat_on), int(cool_on)),
        )
        conn.commit()
        conn.close()

    def get_runs(self, limit=20):
        """Get recent fermentation runs."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM fermentation_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_run(self, run_id):
        """Get a single fermentation run."""
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM fermentation_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_readings(self, run_id, since=None, limit=5000):
        """Get temperature readings for a run.

        Args:
            run_id: The fermentation run ID.
            since: ISO timestamp — only return readings after this time.
            limit: Max number of readings to return.
        """
        conn = self._connect()
        if since:
            rows = conn.execute(
                "SELECT * FROM temperature_readings "
                "WHERE run_id = ? AND timestamp > ? "
                "ORDER BY timestamp ASC LIMIT ?",
                (run_id, since, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM temperature_readings "
                "WHERE run_id = ? ORDER BY timestamp ASC LIMIT ?",
                (run_id, limit),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_latest_reading(self, run_id):
        """Get the most recent reading for a run."""
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM temperature_readings "
            "WHERE run_id = ? ORDER BY timestamp DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None


def _now():
    return datetime.now(timezone.utc).isoformat()
