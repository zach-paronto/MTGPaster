from dataclasses import dataclass, field
from typing import List

from mtgpaster.data.card_face import CardFace


@dataclass
class CardData:
    scryfall_id: str = ""
    oracle_name: str = ""
    oracle_text: str = ""
    faces: List[CardFace] = field(default_factory=list)