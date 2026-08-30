"""
Nettoyage du texte brut issu de l'OCR et conversion en expression SymPy.

Deux couches de tolérance :
1. Nettoyage textuel : caractères unicode courants mal reconnus (×, ÷, −, exposants
   unicode ²³) et préfixes d'énoncé ("f(x) =", "y =") retirés.
2. Parsing tolérant : SymPy avec `implicit_multiplication_application` pour accepter
   "3x" au lieu d'exiger "3*x" — fréquent en sortie OCR qui ne restitue jamais les
   espaces exacts d'une expression manuscrite ou imprimée serrée.
"""
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

x = sp.symbols("x", real=True)

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

_UNICODE_REPLACEMENTS = {
    "×": "*",
    "÷": "/",
    "−": "-",   # signe moins unicode (U+2212), différent du tiret ASCII
    "–": "-",   # tiret demi-cadratin, parfois confondu avec un moins par l'OCR
    "²": "**2",
    "³": "**3",
    "√": "sqrt",
    "π": "pi",
    "∞": "oo",
    ",": ".",   # décimales à la française "3,14" → "3.14" (attention aux listes, rare ici)
}

_PREFIX_PATTERN = re.compile(
    r"^\s*[a-zA-Z]\s*(\(\s*x\s*\))?\s*=\s*", re.IGNORECASE
)  # retire "f(x) =", "f (x)=", "y=", "g(x) =", etc. en tête de chaîne


_LEADING_NOISE_PATTERN = re.compile(r"^[|¦!.,;:'\"\s]+")  # bruit OCR fréquent en tête de ligne


def clean_text(raw_text: str) -> str:
    """Nettoyage purement textuel, avant tentative de parsing."""
    text = raw_text.strip()
    for bad, good in _UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, good)
    text = _LEADING_NOISE_PATTERN.sub("", text)
    text = _PREFIX_PATTERN.sub("", text)
    # espaces multiples / retours à la ligne parasites
    text = re.sub(r"\s+", " ", text).strip()
    return text


class OcrParseError(ValueError):
    """Le texte extrait n'a pas pu être interprété comme une expression mathématique."""


def to_canonical_expression(raw_text: str) -> str:
    """Pipeline complet : nettoyage texte → parsing tolérant SymPy → forme canonique.
    Lève OcrParseError avec un message actionnable si l'expression reste illisible
    (c'est attendu pour des scans de mauvaise qualité — l'utilisateur doit alors
    corriger le texte à la main dans l'interface, jamais de résultat inventé)."""
    cleaned = clean_text(raw_text)
    if not cleaned:
        raise OcrParseError("Aucun texte reconnu dans l'image.")
    try:
        expr = parse_expr(cleaned, local_dict={"x": x}, transformations=_TRANSFORMATIONS, evaluate=True)
    except Exception as e:
        raise OcrParseError(
            f"Le texte extrait « {cleaned} » n'a pas pu être interprété comme une "
            f"fonction de x. Vérifiez/corrigez le texte avant de relancer la correction. "
            f"(détail technique : {e})"
        )
    if expr.free_symbols and x not in expr.free_symbols:
        # une expression sans x du tout (ex: bruit OCR interprété comme un autre
        # symbole) n'est pas une fonction de x exploitable ici ; les constantes
        # pures (free_symbols vide, ex: "f(x) = 2") restent acceptées.
        raise OcrParseError(
            f"Le texte extrait « {cleaned} » ne semble pas définir une fonction de x "
            f"(aucune occurrence de x reconnue). La photo est probablement peu lisible : "
            f"vérifiez/corrigez le texte à la main."
        )
    return str(expr)
