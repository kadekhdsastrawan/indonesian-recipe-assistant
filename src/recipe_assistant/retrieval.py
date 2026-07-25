from collections import defaultdict
from pgvector import Vector
from .config import settings
from .db import connection
from .models import Recipe, RetrievedRecipe


RECIPE_COLUMNS = "recipe_id,dish_name,english_name,region,description,ingredients,instructions,prep_minutes,cook_minutes,servings,tags,allergens,substitutions,tips,source"


def _recipe(row) -> Recipe:
    return Recipe(*row[:15])


def text_search(query: str, limit: int = 10) -> list[RetrievedRecipe]:
    statement = f"SELECT {RECIPE_COLUMNS}, ts_rank_cd(search_vector, websearch_to_tsquery('english', %s)) score FROM recipes WHERE search_vector @@ websearch_to_tsquery('english', %s) ORDER BY score DESC LIMIT %s"
    with connection() as conn, conn.cursor() as cur:
        cur.execute(statement, (query, query, limit))
        return [RetrievedRecipe(_recipe(row), float(row[15]), "text", rank + 1) for rank, row in enumerate(cur.fetchall())]


def vector_search(query: str, embedding: list[float], limit: int = 10) -> list[RetrievedRecipe]:
    statement = f"SELECT {RECIPE_COLUMNS}, 1 - (embedding <=> %s) score FROM recipes WHERE embedding IS NOT NULL ORDER BY embedding <=> %s LIMIT %s"
    with connection() as conn, conn.cursor() as cur:
        # A plain Python list is adapted by psycopg as double precision[];
        # pgvector's cosine operator requires its vector type instead.
        query_vector = Vector(embedding)
        cur.execute(statement, (query_vector, query_vector, limit))
        return [RetrievedRecipe(_recipe(row), float(row[15]), "vector", rank + 1) for rank, row in enumerate(cur.fetchall())]


def reciprocal_rank_fusion(*rankings: list[RetrievedRecipe], k: int = 60) -> list[RetrievedRecipe]:
    totals: dict[str, float] = defaultdict(float)
    records: dict[str, RetrievedRecipe] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            totals[item.recipe.recipe_id] += 1 / (k + rank)
            records[item.recipe.recipe_id] = item
    return [RetrievedRecipe(records[key].recipe, score, "hybrid", rank + 1) for rank, (key, score) in enumerate(sorted(totals.items(), key=lambda item: item[1], reverse=True))]


def rerank(query: str, candidates: list[RetrievedRecipe], limit: int) -> list[RetrievedRecipe]:
    """Cross-encoder re-ranking; retain RRF order if the optional model cannot load."""
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(settings.reranker_model)
        scores = model.predict([(query, item.recipe.document) for item in candidates])
        candidates = [item for _, item in sorted(zip(scores, candidates, strict=True), key=lambda pair: pair[0], reverse=True)]
    except Exception:
        pass
    return [RetrievedRecipe(item.recipe, item.score, item.method, i + 1) for i, item in enumerate(candidates[:limit])]


def retrieve(query: str, query_embedding: list[float] | None, mode: str | None = None, limit: int | None = None) -> list[RetrievedRecipe]:
    mode, limit = mode or settings.retrieval_mode, limit or settings.top_k
    text = text_search(query, max(10, limit))
    if mode == "text" or not query_embedding:
        return text[:limit]
    vector = vector_search(query, query_embedding, max(10, limit))
    if mode == "vector":
        return vector[:limit]
    return rerank(query, reciprocal_rank_fusion(text, vector), limit)
