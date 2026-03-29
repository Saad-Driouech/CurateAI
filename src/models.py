from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Article(BaseModel):
    title: str
    url: HttpUrl
    summary: str
    published_date: datetime | None = None
    source: str
    category: str


class ScoredArticle(BaseModel):
    article: Article
    score: float
    reason: str
    refined_category: str


class PostedArticle(BaseModel):
    message_id: int
    article: Article
    score: float
    reason: str
    category: str
    posted_at: datetime


class Reaction(BaseModel):
    message_id: int
    thumbs_up: int = 0
    thumbs_down: int = 0
    polled_at: datetime


class Preference(BaseModel):
    title: str
    summary: str
    category: str
    reason: str
