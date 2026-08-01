"""
Lecture OCR d'une image d'énoncé — 100% open-source (Tesseract), tourne offline.

Portée honnête de ce module (Phase 2) : Tesseract est un OCR généraliste, PAS un OCR
mathématique spécialisé (type Mathpix). Il lit correctement du texte imprimé sur une
ligne simple ("f(x) = x^3 - 3x + 2"), mais échoue ou fait n'importe quoi sur : les
fractions empilées, les exposants réellement en exposant (vs "^" tapé — confirmé
irrécupérable par simple prétraitement, voir README), les racines carrées avec barre,
l'écriture manuscrite. C'est pourquoi le texte extrait est TOUJOURS présenté à
l'utilisateur pour confirmation/édition avant d'être envoyé au moteur de correction.

Le prétraitement ci-dessous a été mis au point empiriquement sur des photos de cahier
synthétiques dégradées (grille bleue, éclairage inégal, légère rotation, flou léger) :
en isolant chaque facteur de dégradation séparément, l'éclairage inégal s'est révélé
être, de loin, le facteur qui casse le plus l'OCR — d'où l'usage d'un seuillage
ADAPTATIF (qui s'ajuste localement) plutôt qu'un seuil global fixe.
"""
from pathlib import Path
from typing import Union, List, Dict

import numpy as np
import cv2
from PIL import Image
import pytesseract


def _remove_grid_lines(rgb: np.ndarray) -> np.ndarray:
    """Supprime les lignes de grille bleu clair typiques d'un papier de cahier
    (quadrillé/Seyès), en repérant les pixels nettement bleutés et clairs, et en
    les remplaçant par du blanc. Le texte (sombre, tous canaux bas) n'est pas
    affecté même s'il contient un peu de bleu."""
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    min_channel = np.minimum(np.minimum(r, g), b)
    grid_mask = (b - r > 12) & (min_channel > 140)
    cleaned = rgb.copy()
    cleaned[grid_mask] = [255, 255, 255]
    return cleaned


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Corrige une légère rotation (photo prise à main levée) en détectant
    l'orientation du texte via le rectangle englobant minimal des pixels d'encre."""
    inv = 255 - gray
    _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 20:
        return gray  # pas assez de contenu détecté pour estimer un angle fiable
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.3:
        return gray  # rotation négligeable, inutile de ré-échantillonner l'image
    h, w = gray.shape
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def _preprocess(image: Image.Image) -> Image.Image:
    """Pipeline complet : agrandissement, suppression de grille, redressement,
    puis seuillage ADAPTATIF (robuste à un éclairage inégal, contrairement à un
    seuil global fixe — voir docstring du module pour la justification empirique)."""
    rgb = np.array(image.convert("RGB"))

    h, w = rgb.shape[:2]
    if w < 900:
        ratio = 900 / w
        rgb = cv2.resize(rgb, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_LANCZOS4)

    rgb = _remove_grid_lines(rgb)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = _deskew(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        blockSize=41, C=15,
    )
    return Image.fromarray(binary)


def extract_text(image_path: Union[str, Path], single_line: bool = True) -> str:
    """Extrait le texte brut d'une image. `single_line=True` optimise pour un
    énoncé tenant sur une ligne (le cas d'usage principal de cette Phase 2) ;
    passer False pour un bloc de texte multi-lignes (énoncé complet)."""
    image = Image.open(image_path)
    processed = _preprocess(image)
    psm = 7 if single_line else 6  # 7 = ligne unique, 6 = bloc uniforme
    config = f"--psm {psm}"
    text = pytesseract.image_to_string(processed, config=config)
    return text.strip()


_MATH_CHARS = set("0123456789xXyYfFgGhH()+-*/=^.,√π")


def _math_likelihood(text: str) -> float:
    """Score heuristique (0 à 1) de la probabilité qu'une ligne de texte OCR soit
    une expression mathématique plutôt qu'une phrase de consigne ou du bruit :
    proportion de caractères "typiques d'une formule" + bonus pour un signe '='."""
    stripped = text.strip()
    if not stripped:
        return 0.0
    relevant = sum(1 for c in stripped if c in _MATH_CHARS)
    score = relevant / len(stripped)
    if "=" in stripped:
        score += 0.15
    if any(c.isdigit() for c in stripped):
        score += 0.1
    # une ligne très longue et bavarde ("Soit f la fonction définie par...") est
    # probablement une consigne, pas l'expression elle-même : léger malus
    if len(stripped) > 60:
        score -= 0.15
    return max(0.0, min(1.0, score))


def extract_line_candidates(image_path: Union[str, Path], max_candidates: int = 5) -> List[Dict]:
    """Pour une photo pleine page (énoncé pas pré-recadré sur une seule ligne) :
    détecte les lignes de texte via les boîtes englobantes de Tesseract, et les
    classe par vraisemblance d'être une expression mathématique. Ne choisit
    JAMAIS automatiquement à la place de l'utilisateur — renvoie les meilleurs
    candidats pour confirmation, comme le reste du pipeline OCR de ce projet."""
    image = Image.open(image_path)
    processed = _preprocess(image)
    data = pytesseract.image_to_data(processed, config="--psm 6", output_type=pytesseract.Output.DICT)

    lines: Dict[tuple, List[str]] = {}
    boxes: Dict[tuple, List[int]] = {}
    n = len(data["text"])
    for i in range(n):
        word = data["text"][i].strip()
        if not word:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
        x0, y0, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        if key not in boxes:
            boxes[key] = [x0, y0, x0 + w, y0 + h]
        else:
            b = boxes[key]
            boxes[key] = [min(b[0], x0), min(b[1], y0), max(b[2], x0 + w), max(b[3], y0 + h)]

    candidates = []
    for key, words in lines.items():
        text = " ".join(words)
        candidates.append({
            "text": text,
            "score": round(_math_likelihood(text), 3),
            "bbox": boxes[key],
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:max_candidates]
