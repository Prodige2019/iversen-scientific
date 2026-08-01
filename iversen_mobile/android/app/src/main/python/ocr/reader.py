from . import OcrParseError


def extract_line_candidates(*args, **kwargs):
    raise OcrParseError(
        "OCR non disponible sur mobile pour l'instant "
        "(remplacement par ML Kit prevu en Phase 2)."
    )