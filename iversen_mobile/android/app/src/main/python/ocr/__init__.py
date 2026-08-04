"""
Module OCR mobile (Google ML Kit) — voir reader.py pour l'implémentation.
"""
import re

from .reader import extract_text, extract_line_candidates, OcrParseError


def clean_text(text: str) -> str:
    """Nettoyage léger du texte brut lu par l'OCR : espaces superflus."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


_REPLACEMENTS = {
    "×": "*", "÷": "/", "—": "-", "–": "-", "−": "-",
    "‐": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
}


def to_canonical_expression(raw_text: str) -> str:
    """Convertit un texte OCR brut vers une notation que le moteur sait
    analyser. Le moteur accepte déjà la multiplication implicite et "^"
    (voir engine/equations.py), donc peu de transformation est nécessaire
    au-delà du nettoyage des caractères visuellement proches que l'OCR
    confond souvent."""
    text = clean_text(raw_text)
    if not text:
        raise OcrParseError("Aucun texte à convertir.")
    for bad, good in _REPLACEMENTS.items():
        text = text.replace(bad, good)
    return text
