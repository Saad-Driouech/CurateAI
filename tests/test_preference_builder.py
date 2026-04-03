import json
import os
import sqlite3
from datetime import datetime

from src.feedback.preference_builder import build_preferences


def _setup_test_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posted_articles (
            message_id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            score REAL,
            reason TEXT,
            category TEXT,
            posted_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            message_id INTEGER PRIMARY KEY,
            thumbs_up INTEGER DEFAULT 0,
            thumbs_down INTEGER DEFAULT 0,
            polled_at TIMESTAMP NOT NULL
        )
    """)

    conn.execute(
        "INSERT INTO posted_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "https://example.com/liked", "Liked Article", "Good summary", 8.0, "Relevant", "models", datetime.utcnow()),
    )
    conn.execute(
        "INSERT INTO posted_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (2, "https://example.com/disliked", "Disliked Article", "Bad summary", 6.0, "Not great", "other", datetime.utcnow()),
    )
    conn.execute(
        "INSERT INTO reactions VALUES (?, ?, ?, ?)",
        (1, 3, 0, datetime.utcnow()),
    )
    conn.execute(
        "INSERT INTO reactions VALUES (?, ?, ?, ?)",
        (2, 0, 2, datetime.utcnow()),
    )
    conn.commit()
    conn.close()


def test_build_preferences(tmp_path):
    db_path = str(tmp_path / "test.db")
    prefs_path = str(tmp_path / "preferences.json")

    _setup_test_db(db_path)

    os.environ["SQLITE_DB_PATH"] = db_path

    import src.feedback.preference_builder as pb
    original_path = pb.PREFERENCES_PATH
    pb.PREFERENCES_PATH = prefs_path

    try:
        prefs = build_preferences()

        assert len(prefs["liked"]) == 1
        assert len(prefs["disliked"]) == 1
        assert prefs["liked"][0]["title"] == "Liked Article"
        assert prefs["disliked"][0]["title"] == "Disliked Article"

        assert os.path.exists(prefs_path)
        with open(prefs_path) as f:
            saved = json.load(f)
        assert saved == prefs
    finally:
        pb.PREFERENCES_PATH = original_path


def test_empty_reactions(tmp_path):
    db_path = str(tmp_path / "empty.db")
    prefs_path = str(tmp_path / "preferences.json")

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE posted_articles (
            message_id INTEGER PRIMARY KEY, url TEXT, title TEXT,
            summary TEXT, score REAL, reason TEXT, category TEXT, posted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE reactions (
            message_id INTEGER PRIMARY KEY, thumbs_up INTEGER,
            thumbs_down INTEGER, polled_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    os.environ["SQLITE_DB_PATH"] = db_path

    import src.feedback.preference_builder as pb
    original_path = pb.PREFERENCES_PATH
    pb.PREFERENCES_PATH = prefs_path

    try:
        prefs = build_preferences()
        assert prefs["liked"] == []
        assert prefs["disliked"] == []
    finally:
        pb.PREFERENCES_PATH = original_path
