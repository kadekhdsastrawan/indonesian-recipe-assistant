import csv
from pathlib import Path
from .models import Recipe

FIELDS = tuple(Recipe.__dataclass_fields__)


def load_recipes(path: str | Path = "data/recipes_indonesia.csv") -> list[Recipe]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Corpus is missing columns: {', '.join(sorted(missing))}")
        recipes = []
        for row in reader:
            for field in ("prep_minutes", "cook_minutes", "servings"):
                row[field] = int(row[field])
            recipes.append(Recipe(**{field: row[field].strip() if isinstance(row[field], str) else row[field] for field in FIELDS}))
    if not recipes:
        raise ValueError("Corpus must contain at least one recipe")
    if len({recipe.recipe_id for recipe in recipes}) != len(recipes):
        raise ValueError("recipe_id values must be unique")
    return recipes
