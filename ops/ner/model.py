from __future__ import annotations

import os

import spacy

DEFAULT_MODEL = "en_core_web_sm"


def load_model() -> spacy.language.Language:
    model_name = os.environ.get("SPACY_MODEL", DEFAULT_MODEL)
    try:
        return spacy.load(model_name)
    except OSError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            f"spaCy model '{model_name}' not found. Install with: "
            f"python -m spacy download {model_name}"
        ) from exc
