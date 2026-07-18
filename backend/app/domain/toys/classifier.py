from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from .taxonomy import load_toy_taxonomy


@dataclass(frozen=True)
class ToyClassification:
    toy_category: str | None
    content_mechanism: str | None
    safety_flags: tuple[str, ...]
    matched_terms: tuple[str, ...]
    relevance: str


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("#", " ")
    return " ".join(re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).split())


def _contains_phrase(text: str, phrase: str) -> bool:
    normalised = _normalise(phrase)
    return bool(normalised) and f" {normalised} " in f" {text} "


# Rules deliberately require explicit textual evidence. They do not infer age,
# child identity, audience composition, audience geography or product safety.
_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Sensory and fidget toys", ("sensory toy", "sensory toys", "fidget toy", "fidget toys", "zabawki sensoryczne", "zabawkisensoryczne", "sensorytoys", "fidgettoys")),
    ("Plush and soft toys", ("plush toy", "plush toys", "plushie", "plushies", "soft toy", "stuffed toy")),
    ("Blind boxes and collectibles", ("blind box", "blind boxes", "collectible toy", "collectible toys", "zabawki kolekcjonerskie", "collectibletoys", "blindbox")),
    ("Construction toys", ("construction toy", "construction toys", "building set", "building blocks", "klocki konstrukcyjne", "constructiontoys")),
    ("STEM and educational toys", ("stem toy", "stem toys", "educational toy", "educational toys", "learning toy", "zabawki stem", "zabawki edukacyjne", "stemtoys", "educationaltoys", "zabawkiedukacyjne")),
    ("Arts and crafts", ("arts and crafts", "craft toy", "craft kit", "creative kit")),
    ("Dolls and accessories", ("doll", "dolls", "doll accessory", "doll accessories")),
    ("Action figures", ("action figure", "action figures")),
    ("Vehicles and remote-control toys", ("remote control toy", "remote controlled toy", "rc toy", "toy car", "toy vehicle")),
    ("Board games and puzzles", ("board game", "board games", "puzzle", "puzzles")),
    ("Outdoor toys", ("outdoor toy", "outdoor toys", "outdoor play")),
    ("Pretend play", ("pretend play", "role play toy", "roleplay toy")),
    ("Baby and toddler toys", ("baby toy", "baby toys", "toddler toy", "toddler toys", "zabawki dla maluchów")),
    ("Screen-free toys", ("screen free toy", "screen free toys", "screen-free toy", "screen-free toys", "zabawki bez ekranu")),
    ("Electronic and interactive toys", ("electronic toy", "electronic toys", "interactive toy", "interactive toys")),
    ("Licensed character toys", ("licensed character toy", "licensed character toys", "character toy", "character toys")),
    ("Retro and nostalgic toys", ("retro toy", "retro toys", "nostalgic toy", "nostalgic toys")),
    ("Pocket-money toys", ("pocket money toy", "pocket money toys")),
    ("Seasonal and gifting toys", ("gift ideas for children", "giftideasforkids", "toy gift guide", "prezenty dla dzieci", "seasonal toy", "seasonal toys")),
)

_MECHANISM_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Unboxing", ("unboxing", "toy unboxing", "toyunboxing", "rozpakowywanie zabawek")),
    ("Blind reveal", ("blind reveal", "mystery reveal")),
    ("Collection reveal", ("collection reveal", "show my collection")),
    ("Stress test", ("stress test",)),
    ("Durability demonstration", ("durability test", "durability demonstration")),
    ("Parent recommendation", ("parent recommendation", "parents recommend", "toys parents recommend", "polecane przez rodziców")),
    ("Price comparison", ("price comparison", "compare prices")),
    ("Comparison", ("comparison", "versus", " vs ")),
    ("Ranking", ("ranking", "top toys", "ranked")),
    ("Gift guide", ("gift guide", "gift ideas for children", "giftideasforkids", "prezenty dla dzieci")),
    ("Educational demonstration", ("educational demonstration", "learning demonstration")),
    ("Assembly or build", ("assembly", "build with me", "building process")),
    ("Transformation", ("transformation", "before and after")),
    ("ASMR", ("asmr",)),
    ("Restock or scarcity", ("restock", "sold out", "limited stock", "hard to find")),
    ("Challenge", ("challenge",)),
    ("Story-led play", ("story led play", "story-led play")),
    ("Unexpected use", ("unexpected use", "use it as")),
    ("Reaction", ("reaction", "reacts to")),
    ("Product test", ("product test", "toy test", "testing this toy", "toy review", "toyreview", "recenzja zabawki")),
)

_SAFETY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Choking risk", ("choking risk", "choking hazard")),
    ("Unsafe battery use", ("unsafe battery", "battery misuse", "damaged battery")),
    ("Heating or microwaving", ("microwave the toy", "microwaving", "heat the toy")),
    ("Projectile misuse", ("projectile misuse", "shoot at people")),
    ("Water and electricity", ("water and electricity", "electric toy in water")),
    ("Dangerous modification", ("dangerous modification", "dangerous toy hack")),
    ("Unsupported educational claim", ("guaranteed educational result", "guaranteed learning result")),
    ("Unsupported developmental claim", ("guaranteed development", "guarantees development")),
    ("Child distress", ("child distress", "child is distressed")),
    ("Unsupervised toddler demonstration", ("unsupervised toddler",)),
    ("Direct copying of identifiable children", ("copy this child", "copying this child")),
    ("Music-rights uncertainty", ("uncleared music", "music rights unknown")),
    ("Copyright or licensed-character risk", ("copyright risk", "licensed character risk", "unlicensed character")),
)

_CREATOR_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Toy brand", ("toy brand",)),
    ("Toy retailer", ("toy retailer", "toy shop", "toy store")),
    ("Adult toy reviewer", ("adult toy reviewer", "toy reviewer")),
    ("Parent creator", ("parent creator", "mum creator", "mom creator", "dad creator")),
    ("Educator", ("educator", "teacher creator")),
    ("Toy collector", ("toy collector",)),
    ("Play specialist", ("play specialist",)),
    ("Toy designer or inventor", ("toy designer", "toy inventor")),
    ("Family activity creator", ("family activity creator",)),
    ("Entertainment or licensed-IP account", ("licensed ip account", "entertainment account")),
)


def _first_match(text: str, rules: tuple[tuple[str, tuple[str, ...]], ...]) -> tuple[str | None, list[str]]:
    for label, phrases in rules:
        matches = [phrase for phrase in phrases if _contains_phrase(text, phrase)]
        if matches:
            return label, matches
    return None, []


def classify_toy_content(caption: str, hashtags: list[str] | tuple[str, ...]) -> ToyClassification:
    taxonomy = load_toy_taxonomy()
    text = _normalise(" ".join((caption, *hashtags)))
    category, category_matches = _first_match(text, _CATEGORY_RULES)
    mechanism, mechanism_matches = _first_match(text, _MECHANISM_RULES)
    flags: list[str] = []
    safety_matches: list[str] = []
    for label, phrases in _SAFETY_RULES:
        safety_rule_matches = [phrase for phrase in phrases if _contains_phrase(text, phrase)]
        if safety_rule_matches:
            flags.append(label)
            safety_matches.extend(safety_rule_matches)
    assert set(flags) <= set(taxonomy.safety_flags)
    matched_terms = tuple(
        dict.fromkeys((*category_matches, *mechanism_matches, *safety_matches))
    )
    return ToyClassification(
        toy_category=category,
        content_mechanism=mechanism,
        safety_flags=tuple(flags),
        matched_terms=matched_terms,
        relevance="Matched" if category else "Unclassified",
    )


def classify_creator_type(text: str) -> str:
    creator_type, _ = _first_match(_normalise(text), _CREATOR_RULES)
    return creator_type or "Unknown"
