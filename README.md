# Indonesian Recipe Assistant

An English-language RAG chatbot for people who want to cook Indonesian food without needing to speak Bahasa Indonesia. It retrieves from a curated, structured corpus of Indonesian recipes, then produces grounded English cooking guidance with recipe citations.

## Features

- 80 curated Indonesian recipes in English, retaining authentic dish names and regions.
- PostgreSQL full-text, pgvector semantic, and reciprocal-rank-fusion hybrid retrieval.
- Query rewriting, optional cross-encoder re-ranking, and evidence-only answer generation.
- Offline evaluation of all retrieval modes using Hit Rate and MRR, plus an OpenAI LLM-as-judge rubric for relevance, groundedness, and completeness.
- Streamlit chat UI with citations, optional retrieval inspection, and user feedback.
- PostgreSQL event logging and a provisioned Grafana dashboard with seven monitoring charts.
- dlt-backed, idempotent CSV ingestion and complete Docker Compose local environment.

## Quick start

1. Install Docker Desktop and copy configuration:

   ```bash
   cp .env.example .env
   # Add OPENAI_API_KEY to .env for semantic retrieval, generation, and judging.
   ```

2. Start the stack, then ingest the corpus:

   ```bash
   docker compose up --build -d
   docker compose --profile tools run --rm ingest
   ```

3. Open [the chat interface](http://localhost:8501) and [Grafana](http://localhost:3000) (`admin` / the configured password). Run retrieval evaluation with:

   ```bash
   docker compose run --rm app recipe-evaluate
   ```

Without `OPENAI_API_KEY`, text retrieval and a deterministic top-recipe fallback still work. Vector, hybrid semantic search, LLM generation, rewriting, and LLM judging require the key.

## Data and architecture

`data/recipes_indonesia.csv` has stable `recipe_id`, authentic and English names, region, description, ingredients, instructions, timings, servings, tags, allergens, substitutions, tips, and attribution. Every record is original project content (`source: Original project recipe`); there is no runtime web scraping.

Ingestion validates the CSV, constructs one English recipe document per record, produces embeddings where configured, and upserts recipes into PostgreSQL. Postgres maintains a generated English `tsvector` for lexical retrieval and pgvector embeddings for semantic retrieval. Hybrid retrieval combines both rank lists with RRF, then attempts cross-encoder re-ranking.

The application logs chat and retrieval metadata, feedback, evaluation runs, and judge scores. Grafana reads those tables directly. The dashboard includes request volume, P95 latency, errors, Hit Rate, MRR, feedback distribution, and estimated token usage.

## Evaluation

`data/evaluation_queries.json` is the versioned English relevance set. `recipe-evaluate` scores text, vector, and hybrid modes at top-5 using:

- **Hit Rate**: fraction of queries where at least one expected recipe appears.
- **MRR**: reciprocal rank of the first expected recipe, averaged over queries.

The production default is `RETRIEVAL_MODE=hybrid`; retain evaluation output when selecting a different winner. `RecipeAssistant.judge()` compares retrieved evidence and final answers with an LLM rubric. Compare baseline and structured answer prompts and persist individual judge results with:

```bash
docker compose run --rm app recipe-evaluate --judge-prompts
```

Choose the prompt with the best aggregate relevance, groundedness, and completeness result.

## Development and tests

Python 3.12 is required. For local development, install `pip install -e '.[dev]'`, start PostgreSQL via Compose, then run `recipe-ingest` and `pytest`. Dependencies are version-bounded in `pyproject.toml`; Docker images are pinned in `docker-compose.yml`.
