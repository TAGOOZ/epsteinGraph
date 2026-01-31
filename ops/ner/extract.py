from __future__ import annotations

from dataclasses import dataclass

from spacy.language import Language

LABEL_MAP = {
    "PERSON": "person",
    "ORG": "org",
    "GPE": "place",
    "LOC": "place",
    "FAC": "place",
}


@dataclass
class EntityMention:
    text: str
    start_char: int
    end_char: int
    entity_type: str


def extract_entities(text: str, nlp: Language) -> list[EntityMention]:
    doc = nlp(text)
    mentions: list[EntityMention] = []
    for ent in doc.ents:
        entity_type = LABEL_MAP.get(ent.label_, "other")
        mentions.append(
            EntityMention(
                text=ent.text,
                start_char=ent.start_char,
                end_char=ent.end_char,
                entity_type=entity_type,
            )
        )
    return mentions
