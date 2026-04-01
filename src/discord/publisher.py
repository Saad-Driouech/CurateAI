import asyncio
import os
import sqlite3
from datetime import datetime

import discord
from dotenv import load_dotenv

from src.models import ScoredArticle

load_dotenv()

CATEGORY_COLORS = {
    "models": 0x5865F2,
    "research": 0x57F287,
    "tools": 0xFEE75C,
    "safety": 0xED4245,
    "multimodal": 0xEB459E,
    "industry": 0xF47B67,
    "other": 0x99AAB5,
}


def _get_db_path() -> str:
    return os.environ.get("SQLITE_DB_PATH", "data/curator.db")


def _init_db(conn: sqlite3.Connection) -> None:
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
    conn.commit()


def _is_already_posted(conn: sqlite3.Connection, url: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM posted_articles WHERE url = ?", (url,)
    ).fetchone()
    return row is not None


def _build_embed(article: ScoredArticle) -> discord.Embed:
    color = CATEGORY_COLORS.get(article.refined_category, 0x99AAB5)
    embed = discord.Embed(
        title=article.article.title,
        url=str(article.article.url),
        description=article.reason,
        color=color,
    )
    embed.add_field(name="Score", value=f"{article.score}/10", inline=True)
    embed.add_field(name="Category", value=article.refined_category, inline=True)
    embed.add_field(name="Source", value=article.article.source, inline=True)
    embed.set_footer(text="React 👍 or 👎 to help me learn your preferences")
    return embed


async def _publish(scored_articles: list[ScoredArticle]) -> int:
    token = os.environ["DISCORD_BOT_TOKEN"]
    channel_id = int(os.environ["DISCORD_CHANNEL_ID"])

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    posted = 0

    @client.event
    async def on_ready():
        nonlocal posted
        try:
            channel = client.get_channel(channel_id)
            if channel is None:
                channel = await client.fetch_channel(channel_id)

            conn = sqlite3.connect(_get_db_path())
            _init_db(conn)

            for sa in scored_articles:
                url = str(sa.article.url)
                if _is_already_posted(conn, url):
                    continue

                embed = _build_embed(sa)
                msg = await channel.send(embed=embed)
                await msg.add_reaction("👍")
                await msg.add_reaction("👎")

                conn.execute(
                    "INSERT INTO posted_articles (message_id, url, title, summary, score, reason, category, posted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        msg.id,
                        url,
                        sa.article.title,
                        sa.article.summary,
                        sa.score,
                        sa.reason,
                        sa.refined_category,
                        datetime.utcnow(),
                    ),
                )
                posted += 1

            conn.commit()
            conn.close()
        finally:
            await client.close()

    await client.start(token)
    return posted


def publish_articles(scored_articles: list[ScoredArticle]) -> int:
    return asyncio.run(_publish(scored_articles))
