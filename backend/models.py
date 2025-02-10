from pydantic import BaseModel
from typing import Optional, Dict

class CharacterModel(BaseModel):
    id: Optional[str] = None
    name: str
    x: int
    y: int
    hunger: int = 100
    relationships: Dict[str, int] = {} # { "id_other_character": level_relation}

class FoodModel(BaseModel):
    id: Optional[str] = None
    x: int
    y: int