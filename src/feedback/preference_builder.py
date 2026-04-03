import json
import os
import sqlite3

from dotenv import load_dotenv

from src.models import Preference

load_dotenv()

PREFERENCES_PATH = "data/preferences.json"


def _get_db_path() -> str:
    return os.environ.get("SQLITE_DB_PATH", "data/curator.db")


def build_preferences() -> dict:
    conn = sqlite3.connect(_get_db_path())

    liked = conn.execute("""
        SELECT p.title, p.summary, p.category, p.reason
        FROM reactions r
        JOIN posted_articles p ON r.message_id = p.message_id
        WHERE r.thumbs_up > 0
        ORDER BY r.polled_at DESC
        LIMIT 10
    """).fetchall()

    disliked = conn.execute("""
        SELECT p.title, p.summary, p.category, p.reason
        FROM reactions r
        JOIN posted_articles p ON r.message_id = p.message_id
        WHERE r.thumbs_down > 0
        ORDER BY r.polled_at DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    preferences = {
        "liked": [
            Preference(
                title=row[0], summary=row[1], category=row[2], reason=row[3]
            ).model_dump()
            for row in liked
        ],
        "disliked": [
            Preference(
                title=row[0], summary=row[1], category=row[2], reason=row[3]
            ).model_dump()
            for row in disliked
        ],
    }

    with open(PREFERENCES_PATH, "w") as f:
        json.dump(preferences, f, indent=2)

    return preferences
