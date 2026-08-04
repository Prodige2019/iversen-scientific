"""
Lecture de texte sur image, via Google ML Kit Text Recognition (moteur
Android natif, 100% hors ligne) — appelé directement depuis Python grâce
au pont Java de Chaquopy, sans code Kotlin intermédiaire.

Remplace, sur mobile uniquement, l'OCR Tesseract utilisé sur desktop
(cv2 + pytesseract, incompatibles avec Android).
"""
from android.graphics import BitmapFactory
from com.google.mlkit.vision.common import InputImage
from com.google.mlkit.vision.text import TextRecognition
from com.google.mlkit.vision.text.latin import TextRecognizerOptions
from com.google.android.gms.tasks import Tasks


class OcrParseError(Exception):
    pass


_recognizer = None


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    return _recognizer


def _recognize(image_path):
    bitmap = BitmapFactory.decodeFile(image_path)
    if bitmap is None:
        raise OcrParseError("Image illisible (format non reconnu ou fichier corrompu).")
    image = InputImage.fromBitmap(bitmap, 0)
    task = _get_recognizer().process(image)
    # "await" est un mot reserve en Python : on ne peut pas ecrire
    # Tasks.await(task) directement, il faut passer par getattr().
    try:
        return getattr(Tasks, "await")(task)
    except Exception as e:
        raise OcrParseError(f"Échec de la reconnaissance de texte : {e}")


def extract_text(image_path, single_line=True):
    result = _recognize(image_path)
    text = result.getText()
    if not text or not text.strip():
        raise OcrParseError("Aucun texte détecté sur cette image.")
    if single_line:
        lines = [l for l in text.split("\n") if l.strip()]
        return lines[0] if lines else text.strip()
    return text.strip()


def _math_likelihood(text):
    math_chars = set("+-*/=^()<>")
    total = max(len(text), 1)
    digit_ratio = sum(c.isdigit() for c in text) / total
    math_ratio = sum(c in math_chars for c in text) / total
    letter_ratio = sum(c.isalpha() for c in text) / total
    score = 0.5 * digit_ratio + 0.5 * math_ratio
    if letter_ratio > 0.7:
        score *= 0.3
    return round(min(score, 1.0), 2)


def extract_line_candidates(image_path):
    result = _recognize(image_path)
    candidates = []
    for block in result.getTextBlocks():
        for line in block.getLines():
            text = line.getText()
            if not text or not text.strip():
                continue
            bbox = line.getBoundingBox()
            bbox_dict = None
            if bbox is not None:
                bbox_dict = {
                    "left": bbox.left, "top": bbox.top,
                    "right": bbox.right, "bottom": bbox.bottom,
                }
            candidates.append({
                "text": text.strip(),
                "score": _math_likelihood(text),
                "bbox": bbox_dict,
            })
    if not candidates:
        raise OcrParseError("Aucune ligne de texte détectée sur cette photo.")
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
