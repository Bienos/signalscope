from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path


@dataclass(frozen=True)
class ToyTaxonomy:
    search_terms: dict[str, tuple[str, ...]]
    hashtags: tuple[str, ...]
    product_categories: tuple[str, ...]
    content_mechanisms: tuple[str, ...]
    creator_types: tuple[str, ...]
    safety_flags: tuple[str, ...]


@lru_cache(maxsize=1)
def load_toy_taxonomy() -> ToyTaxonomy:
    path = Path(__file__).with_name("seeds.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ToyTaxonomy(
        search_terms={
            language: tuple(values) for language, values in payload["search_terms"].items()
        },
        hashtags=tuple(payload["hashtags"]),
        product_categories=tuple(payload["product_categories"]),
        content_mechanisms=tuple(payload["content_mechanisms"]),
        creator_types=tuple(payload["creator_types"]),
        safety_flags=tuple(payload["safety_flags"]),
    )
