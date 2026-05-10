"""SQLite database setup and connection for annotation pipeline."""
import sqlite3
from pathlib import Path

DATABASE_PATH = Path.home() / ".annotation_pipeline" / "pipeline.db"


def get_connection():
    """Get a database connection with row factory."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            raw_data TEXT,
            stage TEXT NOT NULL DEFAULT 'UPLOAD',
            annotator_id TEXT,
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stage_entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rejection_note TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotators (
            id TEXT PRIMARY KEY,
            items_completed INTEGER DEFAULT 0,
            items_rejected INTEGER DEFAULT 0,
            avg_cycle_time_hrs REAL DEFAULT 0.0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            from_stage TEXT,
            to_stage TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)

    conn.commit()
    conn.close()


def item_counter():
    """Generate sequential item IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    count = cursor.fetchone()[0]
    conn.close()
    return count + 1


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
