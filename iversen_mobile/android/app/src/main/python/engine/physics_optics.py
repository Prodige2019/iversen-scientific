"""
Moteur d'optique — lentille mince convergente, convention algébrique de Descartes.
Étant donné la distance focale f' et la position algébrique de l'objet OA (négative
pour un objet réel placé avant la lentille, sens de propagation de la lumière de
gauche à droite), calcule la position algébrique de l'image OA', le grandissement γ,
et la nature de l'image (réelle/virtuelle, droite/renversée).

Calcul exact via SymPy, même philosophie que le reste du projet.
"""
from dataclasses import dataclass
import sympy as sp
from .equations import parse_math_expression


@dataclass
class OpticsAnalysis:
    f: sp.Expr
    OA: sp.Expr
    OA_prime: sp.Expr
    magnification: sp.Expr
    image_is_real: bool
    image_is_upright: bool


def _parse_value(value_str: str, label: str) -> sp.Expr:
    try:
        return sp.nsimplify(parse_math_expression(value_str))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Valeur illisible pour {label} : « {value_str} ». Détail : {e}")


def analyze_thin_lens(f_str: str, OA_str: str) -> OpticsAnalysis:
    f = _parse_value(f_str, "f'")
    OA = _parse_value(OA_str, "OA")

    if f <= 0:
        raise ValueError(
            f"f' doit être strictement positif pour une lentille convergente (reçu : {f}). "
            "Ce module ne couvre que les lentilles convergentes."
        )
    if OA == 0:
        raise ValueError("OA ne peut pas être nul (l'objet ne peut pas être confondu avec la lentille).")
    if OA > 0:
        raise ValueError(
            f"OA doit être négatif pour un objet réel placé avant la lentille (reçu : {OA}) — "
            "convention algébrique de Descartes, sens de propagation de la lumière de gauche à droite."
        )

    inv_OA_prime = sp.Rational(1, 1) / f + 1 / OA
    if inv_OA_prime == 0:
        raise ValueError(
            "L'image se forme à l'infini pour ces valeurs (objet placé exactement au foyer objet) : "
            "pas de position d'image finie à calculer."
        )
    OA_prime = sp.simplify(1 / inv_OA_prime)
    magnification = sp.simplify(OA_prime / OA)

    return OpticsAnalysis(
        f=f, OA=OA, OA_prime=OA_prime, magnification=magnification,
        image_is_real=bool(OA_prime > 0), image_is_upright=bool(magnification > 0),
    )
