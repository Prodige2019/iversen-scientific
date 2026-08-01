"""
Version mobile de l'OCR : les vraies dependances (cv2, pytesseract) ne
sont pas installees sur Android (voir GUIDE_HORS_LIGNE_CHAQUOPY.md,
Phase 2 - remplacement prevu par Google ML Kit). En attendant, ces
fonctions existent pour que l'import de app.py ne plante pas, mais
renvoient une erreur claire si on les appelle vraiment.
"""


class OcrParseError(Exception):
    pass


def extract_text(*args, **kwargs):
    raise OcrParseError(
        "OCR non disponible sur mobile pour l'instant "
        "(remplacement par ML Kit prevu en Phase 2)."
    )


def clean_text(text):
    return text


def to_canonical_expression(*args, **kwargs):
    raise OcrParseError(
        "OCR non disponible sur mobile pour l'instant "
        "(remplacement par ML Kit prevu en Phase 2)."
    )