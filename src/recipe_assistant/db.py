import json
from contextlib import contextmanager
import psycopg
from pgvector.psycopg import register_vector
from .config import settings


@contextmanager
def connection():
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        yield conn


def log_chat(**event) -> int:
    fields = ("session_id", "query", "rewritten_query", "answer", "retrieval_mode", "recipe_ids", "latency_ms", "prompt_variant", "error", "token_estimate")
    values = [json.dumps(event.get(f)) if f == "recipe_ids" else event.get(f) for f in fields]
    with connection() as conn, conn.cursor() as cur:
        cur.execute(f"INSERT INTO chat_events ({','.join(fields)}) VALUES ({','.join(['%s'] * len(fields))}) RETURNING id", values)
        return cur.fetchone()[0]


def save_feedback(chat_event_id: int, rating: int, comment: str = "") -> None:
    with connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO feedback (chat_event_id, rating, comment) VALUES (%s, %s, %s)", (chat_event_id, rating, comment))
