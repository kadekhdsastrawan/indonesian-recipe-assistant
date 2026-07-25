import argparse
import json
from pathlib import Path
from statistics import mean
from .db import connection
from .rag import RecipeAssistant
from .retrieval import retrieve


def hit_rate(rankings: list[list[str]], expected: list[set[str]]) -> float:
    return mean(bool(set(ranking) & relevant) for ranking, relevant in zip(rankings, expected, strict=True))


def mean_reciprocal_rank(rankings: list[list[str]], expected: list[set[str]]) -> float:
    scores = []
    for ranking, relevant in zip(rankings, expected, strict=True):
        scores.append(next((1 / rank for rank, item in enumerate(ranking, 1) if item in relevant), 0))
    return mean(scores)


def evaluate(path: str | Path = "data/evaluation_queries.json", modes: tuple[str, ...] = ("text", "vector", "hybrid")) -> dict:
    cases = json.loads(Path(path).read_text())
    assistant = RecipeAssistant()
    report = {}
    for mode in modes:
        rankings = []
        for case in cases:
            results = retrieve(case["query"], assistant.embedding(case["query"]), mode=mode, limit=5)
            rankings.append([result.recipe.recipe_id for result in results])
        report[mode] = {"hit_rate": hit_rate(rankings, [set(c["relevant_ids"]) for c in cases]), "mrr": mean_reciprocal_rank(rankings, [set(c["relevant_ids"]) for c in cases]), "rankings": rankings}
        with connection() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO evaluation_runs(name,retrieval_mode,hit_rate,mrr,metadata) VALUES (%s,%s,%s,%s,%s)", ("offline retrieval", mode, report[mode]["hit_rate"], report[mode]["mrr"], json.dumps(report[mode])))
    return report


def evaluate_prompt_variants(path: str | Path = "data/evaluation_queries.json") -> dict:
    """Judge baseline and structured answers; requires OPENAI_API_KEY and an ingested corpus."""
    cases = json.loads(Path(path).read_text())
    assistant = RecipeAssistant()
    report = {}
    for variant in ("baseline", "structured"):
        scores = []
        with connection() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO evaluation_runs(name,retrieval_mode,prompt_variant,metadata) VALUES (%s,%s,%s,%s) RETURNING id", ("LLM judge prompt comparison", "hybrid", variant, "{}"))
            run_id = cur.fetchone()[0]
            for case in cases:
                answer, results, _ = assistant.answer(case["query"], mode="hybrid", prompt_variant=variant)
                score = assistant.judge(case["query"], answer, results)
                scores.append(score)
                cur.execute("INSERT INTO judge_results(evaluation_run_id,query,recipe_id,relevance,groundedness,completeness,rationale) VALUES (%s,%s,%s,%s,%s,%s,%s)", (run_id, case["query"], results[0].recipe.recipe_id if results else None, score.relevance, score.groundedness, score.completeness, score.rationale))
        report[variant] = {key: mean(getattr(score, key) for score in scores) for key in ("relevance", "groundedness", "completeness")}
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default="data/evaluation_queries.json")
    parser.add_argument("--judge-prompts", action="store_true", help="compare baseline and structured prompts with LLM-as-judge")
    args = parser.parse_args()
    result = evaluate_prompt_variants(args.queries) if args.judge_prompts else evaluate(args.queries)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
