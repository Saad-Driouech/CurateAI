from src.fetcher.search import _normalize_result


def test_normalize_basic_result():
    raw = {
        "title": "New GPT-5 Model Released",
        "url": "https://example.com/gpt5",
        "content": "OpenAI released GPT-5 today with major improvements.",
        "published_date": "Mon, 01 Apr 2026 12:00:00 GMT",
    }
    article = _normalize_result(raw, "models")

    assert article.title == "New GPT-5 Model Released"
    assert str(article.url) == "https://example.com/gpt5"
    assert article.source == "example.com"
    assert article.category == "models"
    assert article.published_date is not None


def test_normalize_missing_date():
    raw = {
        "title": "Some Article",
        "url": "https://example.com/article",
        "content": "Content here.",
    }
    article = _normalize_result(raw, "research")

    assert article.published_date is None
    assert article.source == "example.com"


def test_normalize_truncates_summary():
    raw = {
        "title": "Long Article",
        "url": "https://example.com/long",
        "content": "A" * 500,
    }
    article = _normalize_result(raw, "tools")

    assert len(article.summary) == 300
