import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import Article

load_dotenv()

QUERIES = [
    "AI research papers this week",
    "new LLM models released",
    "AI funding and opportunities",
    "AI breakthroughs",
]


def _normalize_result(result: dict, category: str) -> Article:
    published = result.get("published_date")
    if published:
        try:
            published = parsedate_to_datetime(published)
        except (ValueError, TypeError):
            published = None

    return Article(
        title=result["title"],
        url=result["url"],
        summary=result.get("content", "")[:300],
        published_date=published,
        source=urlparse(result["url"]).netloc,
        category=category,
    )


CATEGORY_MAP = {
    "AI research papers this week": "research",
    "new LLM models released": "models",
    "AI funding and opportunities": "opportunities",
    "AI breakthroughs": "breakthroughs",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def _search_query(client: TavilyClient, query: str, max_results: int) -> dict:
    return client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        topic="news",
    )


def fetch_articles(max_per_query: int = 10) -> list[Article]:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    articles: list[Article] = []

    for query in QUERIES:
        response = _search_query(client, query, max_per_query)
        category = CATEGORY_MAP[query]
        for result in response.get("results", []):
            try:
                articles.append(_normalize_result(result, category))
            except (KeyError, ValueError):
                continue

    return articles
