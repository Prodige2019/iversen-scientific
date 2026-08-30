"""
Notation française des ensembles (intervalles, réunions, ensembles finis).

SymPy affiche par défaut les intervalles ouverts avec des parenthèses,
à l'anglo-saxonne : (a, b). La convention utilisée en France (et dans la
francophonie en général) utilise des crochets tournés vers l'extérieur pour
un intervalle ouvert : ]a ; b[. C'est la notation attendue dans une copie
d'élève, donc celle que doit produire une correction générée automatiquement.

Ce module centralise cette mise en forme afin que TOUS les ensembles
affichés dans l'application (ensemble de définition, ensemble de solutions
d'une équation/inéquation, tableaux de signes...) utilisent la même
convention, au lieu de laisser chaque writer réinventer sa propre règle
(source du bug initial : la parenthèse restait affichée à certains endroits
et pas à d'autres).
"""
from typing import List

import sympy as sp
from sympy import latex, oo


def _interval_latex(interval: sp.Interval) -> str:
    """Un seul intervalle -> notation française, bornes infinies toujours
    représentées par un crochet ouvert (]−∞ ; ... ou ... ; +∞[)."""
    left = "]" if (interval.left_open or interval.start == -oo) else "["
    right = "[" if (interval.right_open or interval.end == oo) else "]"
    start = "-\\infty" if interval.start == -oo else latex(interval.start)
    end = "+\\infty" if interval.end == oo else latex(interval.end)
    return f"\\left{left}{start} \\, ; \\, {end}\\right{right}"


def _pieces(s: sp.Set) -> List[sp.Set]:
    """Décompose une Union en sous-ensembles triés de gauche à droite (par
    borne inférieure) pour un affichage dans l'ordre naturel sur l'axe."""
    if isinstance(s, sp.Union):
        pieces = list(s.args)
    else:
        pieces = [s]

    def _sort_key(piece):
        if isinstance(piece, sp.Interval):
            try:
                return float(piece.start) if piece.start != -oo else float("-inf")
            except (TypeError, ValueError):
                return float("-inf")
        return float("-inf")

    return sorted(pieces, key=_sort_key)


def french_set_latex(s: sp.Set) -> str:
    """Représentation LaTeX (notation française, crochets) d'un ensemble
    SymPy quelconque : intervalle, union d'intervalles, ensemble fini, ℝ,
    ensemble vide. Utilisé pour l'ensemble de définition d'une fonction,
    l'ensemble des solutions d'une (in)équation, et les tableaux de signes."""
    if s == sp.EmptySet:
        return "\\varnothing"
    if s == sp.S.Reals or s == sp.Interval(-oo, oo):
        return "\\mathbb{R}"

    if isinstance(s, sp.FiniteSet):
        elements = " \\, ; \\, ".join(latex(e) for e in s.args)
        return f"\\left\\{{ {elements} \\right\\}}"

    if isinstance(s, sp.Interval):
        return _interval_latex(s)

    if isinstance(s, sp.Union):
        parts = _pieces(s)
        return " \\cup ".join(french_set_latex(p) for p in parts)

    # Repli : type d'ensemble non géré explicitement (ex: Complement non
    # résolu). On ne perd pas l'information, mais on corrige au moins les
    # parenthèses les plus évidentes vers la notation française.
    fallback = latex(s)
    return (
        fallback
        .replace("\\left(", "\\left]")
        .replace("\\right)", "\\right[")
    )
