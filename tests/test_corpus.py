from recipe_assistant.corpus import load_recipes


def test_corpus_has_unique_structured_recipes():
    recipes = load_recipes()
    assert len(recipes) >= 80
    assert len({r.recipe_id for r in recipes}) == len(recipes)
    assert "Ingredients:" in recipes[0].document
