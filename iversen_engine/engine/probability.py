"""
Moteur pour la loi binomiale B(n, p) — même philosophie que le reste du projet :
calcul exact (fractions SymPy, pas de flottants approximatifs) et déterministe.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import sympy as sp
from .equations import parse_math_expression


@dataclass
class BinomialAnalysis:
    n: int
    p: sp.Expr
    k: Optional[int]                        # valeur ponctuale demandée, si fournie
    proba_exact: Optional[sp.Expr] = None    # P(X = k), fraction exacte
    proba_exact_decimal: Optional[float] = None
    cumulative_le: Optional[sp.Expr] = None  # P(X <= k)
    cumulative_ge: Optional[sp.Expr] = None  # P(X >= k)
    expectation: sp.Expr = field(default=None)
    variance: sp.Expr = field(default=None)
    std_dev: sp.Expr = field(default=None)
    distribution_table: List["tuple[int, sp.Expr]"] = field(default_factory=list)


def _validate_n_p(n: int, p_str: str) -> "tuple[int, sp.Expr]":
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n doit être un entier strictement positif (reçu : {n}).")
    try:
        p = sp.nsimplify(parse_math_expression(p_str))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Probabilité p illisible : « {p_str} ». Détail : {e}")
    if not (p.is_real and 0 <= p <= 1):
        raise ValueError(f"p doit être un réel compris entre 0 et 1 (reçu : {p}).")
    return n, p


def _proba_exact(n: int, p: sp.Expr, k: int) -> sp.Expr:
    if not (0 <= k <= n):
        raise ValueError(f"k doit être compris entre 0 et n={n} (reçu : {k}).")
    return sp.binomial(n, k) * p**k * (1 - p)**(n - k)


def analyze_binomial(n: int, p_str: str, k: Optional[int] = None) -> BinomialAnalysis:
    n, p = _validate_n_p(n, p_str)

    expectation = sp.nsimplify(n * p)
    variance = sp.nsimplify(n * p * (1 - p))
    std_dev = sp.sqrt(variance)

    distribution_table = [(i, sp.simplify(_proba_exact(n, p, i))) for i in range(n + 1)]

    result = BinomialAnalysis(
        n=n, p=p, k=k,
        expectation=expectation, variance=variance, std_dev=std_dev,
        distribution_table=distribution_table,
    )

    if k is not None:
        proba = sp.simplify(_proba_exact(n, p, k))
        result.proba_exact = proba
        result.proba_exact_decimal = float(proba)
        result.cumulative_le = sp.simplify(sum(pr for i, pr in distribution_table if i <= k))
        result.cumulative_ge = sp.simplify(sum(pr for i, pr in distribution_table if i >= k))

    return result
