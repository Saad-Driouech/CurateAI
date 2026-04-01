import os

import anthropic
import instructor
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.models import Article, ScoredArticle

load_dotenv()

SYSTEM_PROMPT = """You are an AI news curator for an AI/ML researcher and engineer.

Their interests:
- New model releases (LLMs, multimodal, vision, etc.)
- Research papers and breakthroughs
- Open-source AI tools and frameworks
- AI safety and alignment research
- Multimodal systems (vision-language, audio, etc.)
- Industry opportunities (partnerships, grants, competitions — not job listings)

Score each article from 0 to 10 based on how relevant and valuable it is to this user.
- 8-10: Highly relevant, directly about their core interests
- 6-7: Somewhat relevant, tangentially related
- 3-5: Low relevance, generic AI news
- 0-2: Not relevant (marketing fluff, unrelated tech, job posts)

Also assign a refined category from: [models, research, tools, safety, multimodal, industry, other].
"""


class ArticleScore(BaseModel):
    score: float = Field(ge=0, le=10, description="Relevance score from 0 to 10")
    reason: str = Field(description="One-line reason for the score")
    refined_category: str = Field(description="One of: models, research, tools, safety, multimodal, industry, other")


def _build_client() -> instructor.Instructor:
    return instructor.from_anthropic(
        anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    )


def score_article(client: instructor.Instructor, article: Article) -> ScoredArticle:
    result = client.chat.completions.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Title: {article.title}\nSource: {article.source}\nCategory: {article.category}\nSummary: {article.summary}",
            }
        ],
        response_model=ArticleScore,
    )
    return ScoredArticle(
        article=article,
        score=result.score,
        reason=result.reason,
        refined_category=result.refined_category,
    )


def filter_articles(
    articles: list[Article],
    min_score: float = 6.0,
    max_results: int = 10,
) -> list[ScoredArticle]:
    client = _build_client()
    scored = []
    for article in articles:
        result = score_article(client, article)
        if result.score >= min_score:
            scored.append(result)

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:max_results]
