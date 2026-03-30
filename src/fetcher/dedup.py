import os
import sqlite3
from datetime import datetime, timedelta

from dotenv import load_dotenv

from src.models import Article

load_dotenv()


def _get_db_path() -> str:
    return os.environ.get("SQLITE_DB_PATH", "data/curator.db")


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_articles (
            url TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            first_seen TIMESTAMP NOT NULL
        )
    """)
    conn.commit()


def filter_new(articles: list[Article]) -> list[Article]:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    _init_db(conn)

    cutoff = datetime.utcnow() - timedelta(days=7)
    conn.execute("DELETE FROM seen_articles WHERE first_seen < ?", (cutoff,))
    conn.commit()

    seen = {
        row[0]
        for row in conn.execute("SELECT url FROM seen_articles").fetchall()
    }

    new_articles = []
    for article in articles:
        url = str(article.url)
        if url not in seen:
            new_articles.append(article)
            seen.add(url)
            conn.execute(
                "INSERT OR IGNORE INTO seen_articles (url, title, first_seen) VALUES (?, ?, ?)",
                (url, article.title, datetime.utcnow()),
            )

    conn.commit()
    conn.close()
    return new_articles
