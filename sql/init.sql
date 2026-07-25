CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS recipes (
  recipe_id TEXT PRIMARY KEY, dish_name TEXT NOT NULL, english_name TEXT NOT NULL,
  region TEXT NOT NULL, description TEXT NOT NULL, ingredients TEXT NOT NULL,
  instructions TEXT NOT NULL, prep_minutes INTEGER NOT NULL, cook_minutes INTEGER NOT NULL,
  servings INTEGER NOT NULL, tags TEXT NOT NULL, allergens TEXT NOT NULL,
  substitutions TEXT NOT NULL, tips TEXT NOT NULL, source TEXT NOT NULL,
  document TEXT NOT NULL, search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', document)) STORED,
  embedding vector(1536), ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS recipes_search_idx ON recipes USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS recipes_embedding_idx ON recipes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TABLE IF NOT EXISTS chat_events (
  id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), session_id TEXT,
  query TEXT NOT NULL, rewritten_query TEXT, answer TEXT, retrieval_mode TEXT, recipe_ids JSONB,
  latency_ms INTEGER, prompt_variant TEXT, error TEXT, token_estimate INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS retrieval_events (
  id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), query TEXT NOT NULL,
  retrieval_mode TEXT NOT NULL, recipe_id TEXT NOT NULL, rank INTEGER NOT NULL, score REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
  id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), chat_event_id BIGINT REFERENCES chat_events(id),
  rating SMALLINT NOT NULL CHECK (rating IN (-1,1)), comment TEXT
);
CREATE TABLE IF NOT EXISTS evaluation_runs (
  id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), name TEXT NOT NULL,
  retrieval_mode TEXT NOT NULL, prompt_variant TEXT, hit_rate REAL, mrr REAL, metadata JSONB
);
CREATE TABLE IF NOT EXISTS judge_results (
  id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), evaluation_run_id BIGINT REFERENCES evaluation_runs(id),
  query TEXT NOT NULL, recipe_id TEXT, relevance REAL, groundedness REAL, completeness REAL, rationale TEXT
);
