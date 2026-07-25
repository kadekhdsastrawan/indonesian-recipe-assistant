import json
import time
from openai import OpenAI
from .config import settings
from .db import log_chat
from .models import JudgeScore, RetrievedRecipe
from .retrieval import retrieve


BASELINE_PROMPT = "Answer the user's cooking question in English using only the supplied recipes. Cite recipe IDs. If no recipe supports the answer, say so."
STRUCTURED_PROMPT = """You are an English-language Indonesian cooking assistant. Use only the supplied recipe records. Give a helpful, concise answer with dish name, ingredients, numbered steps, time/servings when relevant, substitutions/tips, and [recipe_id] citations. Never invent a recipe or fact; say the corpus lacks evidence instead."""


class RecipeAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def rewrite(self, query: str, history: list[dict] | None = None) -> str:
        if not self.client or not history:
            return query
        prompt = "Rewrite this follow-up as a standalone concise English recipe search query. Return only the query.\nHistory:\n" + "\n".join(f"{m['role']}: {m['content']}" for m in history[-4:]) + f"\nUser: {query}"
        return self.client.chat.completions.create(model=settings.chat_model, messages=[{"role": "user", "content": prompt}], temperature=0).choices[0].message.content.strip()

    def embedding(self, query: str) -> list[float] | None:
        if not self.client:
            return None
        return self.client.embeddings.create(model=settings.embedding_model, input=query).data[0].embedding

    @staticmethod
    def context(results: list[RetrievedRecipe]) -> str:
        return "\n\n".join(f"[recipe_id: {x.recipe.recipe_id}]\n{x.recipe.document}" for x in results)

    def answer(self, query: str, history: list[dict] | None = None, mode: str | None = None, prompt_variant: str = "structured") -> tuple[str, list[RetrievedRecipe], int]:
        started = time.perf_counter()
        rewritten = self.rewrite(query, history)
        results = retrieve(rewritten, self.embedding(rewritten), mode)
        if not results:
            answer = "I could not find a matching recipe in the current Indonesian recipe collection. Try a dish name or ingredient."
        elif not self.client:
            recipe = results[0].recipe
            answer = f"{recipe.dish_name} — {recipe.english_name}\n\nIngredients: {recipe.ingredients}\n\nSteps: {recipe.instructions}\n\nTips: {recipe.tips}\n\nSource: [{recipe.recipe_id}]"
        else:
            system = STRUCTURED_PROMPT if prompt_variant == "structured" else BASELINE_PROMPT
            answer = self.client.chat.completions.create(model=settings.chat_model, temperature=0.2, messages=[{"role": "system", "content": system}, {"role": "user", "content": f"Question: {query}\n\nRecipes:\n{self.context(results)}"}]).choices[0].message.content
        event_id = log_chat(session_id=None, query=query, rewritten_query=rewritten, answer=answer, retrieval_mode=mode or settings.retrieval_mode, recipe_ids=[x.recipe.recipe_id for x in results], latency_ms=round((time.perf_counter()-started)*1000), prompt_variant=prompt_variant, token_estimate=len(answer)//4)
        return answer, results, event_id

    def judge(self, query: str, answer: str, results: list[RetrievedRecipe]) -> JudgeScore:
        if not self.client:
            return JudgeScore(0, 0, 0, "LLM judge requires OPENAI_API_KEY")
        prompt = "Score 0 to 1 and return JSON only with relevance, groundedness, completeness, rationale. Judge the answer against the provided retrieved recipes.\n" + json.dumps({"query": query, "answer": answer, "recipes": [r.recipe.document for r in results]})
        response = self.client.chat.completions.create(model=settings.chat_model, response_format={"type": "json_object"}, messages=[{"role": "system", "content": "You are a strict RAG evaluator."}, {"role": "user", "content": prompt}], temperature=0)
        return JudgeScore.from_dict(json.loads(response.choices[0].message.content))
