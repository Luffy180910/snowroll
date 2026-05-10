-- Xueqiu posts schema (SQLite-flavored).
-- For PostgreSQL, see schema_pg.sql (which is auto-derived but uses
-- BIGSERIAL / TEXT semantics natively).

CREATE TABLE IF NOT EXISTS posts (
    id                  INTEGER PRIMARY KEY,
    symbol              TEXT,
    user_id             INTEGER,
    user_name           TEXT,
    user_followers      INTEGER DEFAULT 0,
    created_at          TEXT,
    title               TEXT,
    text                TEXT,
    mentioned_symbols   TEXT,
    reply_count         INTEGER DEFAULT 0,
    retweet_count       INTEGER DEFAULT 0,
    fav_count           INTEGER DEFAULT 0,
    like_count          INTEGER DEFAULT 0,
    view_count          INTEGER DEFAULT 0,
    source_api          TEXT,
    category            TEXT,
    crawled_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_posts_symbol         ON posts(symbol);
CREATE INDEX IF NOT EXISTS idx_posts_created        ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_mentioned      ON posts(mentioned_symbols);
CREATE INDEX IF NOT EXISTS idx_posts_user           ON posts(user_id);

-- Reserved for future: comments table (not implemented yet).
-- CREATE TABLE IF NOT EXISTS comments (...);

-- Reserved for future: sentiment scores table (NLP downstream).
-- See schema_sentiment.sql.
