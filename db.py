"""
db.py — SQLite database helpers for family profiles.

Auto-creates nutrition.db and the family_profiles table on first run.
No external ORM — uses the stdlib sqlite3 module directly.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "nutrition.db")


def _get_connection() -> sqlite3.Connection:
    """Return a sqlite3 connection with row_factory set to dict-like Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the family_profiles table if it does not yet exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS family_profiles (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                name                 TEXT    NOT NULL,
                age                  INTEGER NOT NULL,
                gender               TEXT    NOT NULL,
                weight_kg            REAL    NOT NULL,
                height_cm            REAL    NOT NULL,
                activity_level       TEXT    NOT NULL DEFAULT 'Moderately Active',
                dietary_restrictions TEXT    NOT NULL DEFAULT '',
                health_goals         TEXT    NOT NULL DEFAULT '',
                created_at           TEXT    NOT NULL
            )
        """)
        conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ─────────────────────────────────────────────────────────────────
#  CRUD helpers
# ─────────────────────────────────────────────────────────────────

def get_all_profiles() -> list[dict]:
    """Return all profiles ordered by name."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM family_profiles ORDER BY name"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_profile(profile_id: int) -> dict | None:
    """Return a single profile dict, or None if not found."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM family_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def create_profile(data: dict) -> int:
    """Insert a new profile; return the new row id."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO family_profiles
                (name, age, gender, weight_kg, height_cm,
                 activity_level, dietary_restrictions, health_goals, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                int(data["age"]),
                data["gender"],
                float(data["weight_kg"]),
                float(data["height_cm"]),
                data.get("activity_level", "Moderately Active"),
                data.get("dietary_restrictions", ""),
                data.get("health_goals", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    return cursor.lastrowid


def update_profile(profile_id: int, data: dict) -> bool:
    """Update an existing profile. Returns True if a row was changed."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE family_profiles SET
                name                 = ?,
                age                  = ?,
                gender               = ?,
                weight_kg            = ?,
                height_cm            = ?,
                activity_level       = ?,
                dietary_restrictions = ?,
                health_goals         = ?
            WHERE id = ?
            """,
            (
                data["name"],
                int(data["age"]),
                data["gender"],
                float(data["weight_kg"]),
                float(data["height_cm"]),
                data.get("activity_level", "Moderately Active"),
                data.get("dietary_restrictions", ""),
                data.get("health_goals", ""),
                profile_id,
            ),
        )
        conn.commit()
    return cursor.rowcount > 0


def delete_profile(profile_id: int) -> bool:
    """Delete a profile by id. Returns True if a row was removed."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM family_profiles WHERE id = ?", (profile_id,)
        )
        conn.commit()
    return cursor.rowcount > 0
