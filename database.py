import sqlite3
import os
from datetime import datetime

DB_PATH = "grimoire.db"


def init_db():
    """Create the database and table if they don't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT,
            source_type TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_summary(source_name, source_type, notes):
    """Save a completed summary to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO summaries (source_name, source_type, notes, created_at) VALUES (?, ?, ?, ?)",
        (source_name, source_type, notes, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_summaries():
    """Fetch every saved summary, most recent first."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, source_name, source_type, notes, created_at FROM summaries ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_summary_count_by_date():
    """Count how many summaries were made per day — used for the dashboard chart."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM summaries
        GROUP BY day
        ORDER BY day
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_source_type_breakdown():
    """Count summaries by source type (pdf, txt, audio, youtube) — used for a pie chart."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_type, COUNT(*) as count
        FROM summaries
        GROUP BY source_type
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {os.path.abspath(DB_PATH)}")