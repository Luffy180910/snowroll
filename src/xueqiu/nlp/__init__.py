"""Downstream NLP / sentiment analysis layer — RESERVED FOR FUTURE.

This package is the agreed-upon home for sentiment analysis on the crawled
posts. It is intentionally empty for now. The expected shape:

    nlp/
    ├── base.py           # SentimentScorer ABC: score(text) -> SentimentScore
    ├── lexicon.py        # dictionary-based scorer (snownlp, custom finance lexicon)
    ├── transformer.py    # transformer-based scorer (FinBERT-zh, Erlangshen-Sentiment)
    ├── pipeline.py       # ScorePipeline: read posts from storage, score, write back
    └── schema_sentiment.sql  # sentiment table schema

Integration sketch:

    from xueqiu.storage import create_storage
    from xueqiu.nlp import LexiconScorer, ScorePipeline

    with create_storage() as storage:
        scorer = LexiconScorer()
        ScorePipeline(scorer, storage).score_unscored(batch_size=500)

The pipeline reads from `posts` table, writes to a `sentiment` table keyed
by post.id, so re-running with a better model is just a backfill.
"""
