"""dlt-backed corpus ingestion into PostgreSQL/pgvector."""
import argparse
from pathlib import Path
import dlt
from openai import OpenAI
from pgvector import Vector
from psycopg import sql
from .config import settings
from .corpus import load_recipes
from .db import connection


def embed(texts: list[str]) -> list[list[float] | None]:
    if not settings.openai_api_key:
        return [None] * len(texts)
    client = OpenAI(api_key=settings.openai_api_key)
    return [item.embedding for item in client.embeddings.create(model=settings.embedding_model, input=texts).data]


def ingest(corpus_path: str | Path = "data/recipes_indonesia.csv") -> int:
    recipes = load_recipes(corpus_path)
    vectors = embed([recipe.document for recipe in recipes])
    columns = list(recipes[0].__dataclass_fields__) + ["document", "embedding"]
    statement = sql.SQL("INSERT INTO recipes ({}) VALUES ({}) ON CONFLICT (recipe_id) DO UPDATE SET {}") .format(
        sql.SQL(",").join(map(sql.Identifier, columns)), sql.SQL(",").join(sql.Placeholder() for _ in columns),
        sql.SQL(",").join(sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c)) for c in columns if c != "recipe_id"),
    )
    with connection() as conn, conn.cursor() as cur:
        for recipe, vector in zip(recipes, vectors, strict=True):
            pg_embedding = Vector(vector) if vector is not None else None
            cur.execute(statement, [getattr(recipe, field) for field in recipe.__dataclass_fields__] + [recipe.document, pg_embedding])
    return len(recipes)


def dlt_ingest(corpus_path: str | Path = "data/recipes_indonesia.csv") -> int:
    """Expose corpus rows as a dlt resource for lineage/normalization demos."""
    @dlt.resource(name="recipe_source", write_disposition="replace")
    def rows():
        for recipe in load_recipes(corpus_path):
            yield {**recipe.__dict__, "document": recipe.document}
    pipeline = dlt.pipeline(pipeline_name="recipe_source_audit", destination="filesystem", dataset_name="recipe")
    pipeline.run(rows())
    return ingest(corpus_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/recipes_indonesia.csv")
    parser.add_argument("--with-dlt-audit", action="store_true")
    args = parser.parse_args()
    print(f"Ingested {dlt_ingest(args.corpus) if args.with_dlt_audit else ingest(args.corpus)} recipes")


if __name__ == "__main__":
    main()
