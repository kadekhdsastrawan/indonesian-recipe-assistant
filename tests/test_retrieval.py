from recipe_assistant.models import Recipe, RetrievedRecipe
from recipe_assistant.retrieval import reciprocal_rank_fusion


def item(recipe_id, score=1):
    return RetrievedRecipe(Recipe(recipe_id, recipe_id, recipe_id, "Java", "desc", "i", "s", 1, 1, 1, "", "", "", "", "source"), score, "test")


def test_rrf_promotes_items_found_by_multiple_searches():
    merged = reciprocal_rank_fusion([item("a"), item("b")], [item("b"), item("c")])
    assert merged[0].recipe.recipe_id == "b"
