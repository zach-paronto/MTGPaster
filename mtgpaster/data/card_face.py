from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class CardFace:
    scryfall_id: str = ""
    image_url: str = ""
    thumbnail_url: str = ""
    side: Enum('FRONT', 'BACK') = 'FRONT'