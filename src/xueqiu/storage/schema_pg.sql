-- Xueqiu posts schema (PostgreSQL).

CREATE TABLE IF NOT EXISTS posts (
    id                  BIGINT PRIMARY KEY,
    symbol              TEXT,
    user_id             BIGINT,
    user_name           TEXT,
    user_followers      INTEGER DEFAULT 0,
    created_at          TIMESTAMP,
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
    crawled_at          TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_symbol         ON posts(symbol);
CREATE INDEX IF NOT EXISTS idx_posts_created        ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_mentioned      ON posts(mentioned_symbols);
CREATE INDEX IF NOT EXISTS idx_posts_user           ON posts(user_id);
