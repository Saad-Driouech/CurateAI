import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

import discord
from dotenv import load_dotenv

load_dotenv()


def _get_db_path() -> str:
    return os.environ.get("SQLITE_DB_PATH", "data/curator.db")


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            message_id INTEGER PRIMARY KEY,
            thumbs_up INTEGER DEFAULT 0,
            thumbs_down INTEGER DEFAULT 0,
            polled_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()


async def _poll(hours: int = 48) -> int:
    token = os.environ["DISCORD_BOT_TOKEN"]
    channel_id = int(os.environ["DISCORD_CHANNEL_ID"])

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    updated = 0

    @client.event
    async def on_ready():
        nonlocal updated
        try:
            channel = client.get_channel(channel_id)
            if channel is None:
                channel = await client.fetch_channel(channel_id)

            conn = sqlite3.connect(_get_db_path())
            _init_db(conn)

            posted_ids = {
                row[0]
                for row in conn.execute(
                    "SELECT message_id FROM posted_articles WHERE posted_at > ?",
                    (datetime.utcnow() - timedelta(hours=hours),),
                ).fetchall()
            }

            after = datetime.utcnow() - timedelta(hours=hours)
            async for msg in channel.history(after=after, limit=200):
                if msg.id not in posted_ids:
                    continue

                thumbs_up = 0
                thumbs_down = 0
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "👍":
                        thumbs_up = reaction.count - 1  # subtract bot's own reaction
                    elif str(reaction.emoji) == "👎":
                        thumbs_down = reaction.count - 1

                conn.execute(
                    "INSERT OR REPLACE INTO reactions (message_id, thumbs_up, thumbs_down, polled_at) VALUES (?, ?, ?, ?)",
                    (msg.id, thumbs_up, thumbs_down, datetime.utcnow()),
                )
                updated += 1

            conn.commit()
            conn.close()
        finally:
            await client.close()

    await client.start(token)
    return updated


def poll_reactions(hours: int = 48) -> int:
    return asyncio.run(_poll(hours))
