from dataclasses import dataclass
from typing import Any


@dataclass
class Recipe:
    recipe_id: str
    dish_name: str
    english_name: str
    region: str
    description: str
    ingredients: str
    instructions: str
    prep_minutes: int
    cook_minutes: int
    servings: int
    tags: str
    allergens: str
    substitutions: str
    tips: str
    source: str

    @property
    def document(self) -> str:
        return "\n".join((
            f"{self.dish_name} ({self.english_name}) — {self.region}", self.description,
            f"Ingredients: {self.ingredients}", f"Instructions: {self.instructions}",
            f"Tags: {self.tags}. Allergens: {self.allergens}.",
            f"Substitutions: {self.substitutions}. Tips: {self.tips}",
        ))


@dataclass
class RetrievedRecipe:
    recipe: Recipe
    score: float
    method: str
    rank: int = 0


@dataclass
class JudgeScore:
    relevance: float
    groundedness: float
    completeness: float
    rationale: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "JudgeScore":
        return cls(**{key: value.get(key, 0) for key in cls.__annotations__})
