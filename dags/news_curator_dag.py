from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "curateai",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="news_curator",
    default_args=default_args,
    description="Fetch, filter, and publish AI news to Discord",
    schedule_interval="0 6,18 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["ai", "news", "curator"],
) as dag:

    def _poll_feedback(**kwargs):
        pass

    def _fetch_news(**kwargs):
        from src.fetcher.search import fetch_articles
        from src.fetcher.dedup import filter_new

        articles = fetch_articles()
        new_articles = filter_new(articles)
        kwargs["ti"].xcom_push(
            key="articles",
            value=[a.model_dump_json() for a in new_articles],
        )

    def _filter_news(**kwargs):
        from src.filter.scorer import filter_articles
        from src.models import Article

        ti = kwargs["ti"]
        raw_articles = ti.xcom_pull(task_ids="fetch_news", key="articles")
        articles = [Article.model_validate_json(a) for a in raw_articles]
        scored = filter_articles(articles)
        ti.xcom_push(
            key="scored_articles",
            value=[s.model_dump_json() for s in scored],
        )

    def _publish_news(**kwargs):
        from src.discord.publisher import publish_articles
        from src.models import ScoredArticle

        ti = kwargs["ti"]
        raw_scored = ti.xcom_pull(task_ids="filter_news", key="scored_articles")
        scored = [ScoredArticle.model_validate_json(s) for s in raw_scored]
        count = publish_articles(scored)
        print(f"Published {count} articles to Discord")

    poll_feedback = PythonOperator(
        task_id="poll_feedback",
        python_callable=_poll_feedback,
    )

    fetch_news = PythonOperator(
        task_id="fetch_news",
        python_callable=_fetch_news,
    )

    filter_news = PythonOperator(
        task_id="filter_news",
        python_callable=_filter_news,
    )

    publish_news = PythonOperator(
        task_id="publish_news",
        python_callable=_publish_news,
    )

    poll_feedback >> fetch_news >> filter_news >> publish_news
