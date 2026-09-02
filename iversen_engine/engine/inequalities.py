"""
Moteur de résolution d'inéquations — réutilise la classification et le calcul du
discriminant de engine/equations.py, et s'appuie sur sp.solveset (SymPy) pour la
résolution finale, qui est fiable et bien testée par SymPy lui-même pour les
inéquations polynomiales et au-delà.
"""
from tokenize import TokenError
from dataclasses import dataclass, field
from typing import List, Optional
import sympy as sp
from sympy.calculus.util import continuous_domain
from .equations import x, parse_equation, normalize_variable_case, parse_math_expression, _has_radical


RELATION_SYMBOLS = {
    sp.StrictGreaterThan: ">",
    sp.GreaterThan: "≥",
    sp.StrictLessThan: "<",
    sp.LessThan: "≤",
}


@dataclass
class InequalityAnalysis:
    lhs: sp.Expr
    rhs: sp.Expr
    relop: str                     # ">", "≥", "<", "≤"
    normalized_expr: sp.Expr       # lhs - rhs
    kind: str                      # "linéaire" | "quadratique" | "générale"
    degree: Optional[int]
    coefficients: List[sp.Expr] = field(default_factory=list)
    discriminant: Optional[sp.Expr] = None
    roots: List[sp.Expr] = field(default_factory=list)
    solution_set: Optional[sp.Set] = None
    domain: Optional[sp.Set] = None  # renseigné pour kind == "avec racine" : domaine de validité


def _parse_inequality(inequality_str: str):
    """Parse une chaîne 'lhs OP rhs' avec OP dans {<, <=, >, >=}. Renvoie l'objet
    Relational SymPy correspondant."""
    try:
        rel = parse_math_expression(normalize_variable_case(inequality_str.strip()), {"x": x})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Inéquation illisible : « {inequality_str} ». Détail : {e}")
    if not isinstance(rel, sp.core.relational.Relational) or isinstance(rel, (sp.Eq, sp.Ne)):
        raise ValueError(
            f"« {inequality_str} » ne ressemble pas à une inéquation "
            f"(attendu : une expression avec <, <=, > ou >=)."
        )
    return rel


def solve_inequality(inequality_str: str) -> InequalityAnalysis:
    rel = _parse_inequality(inequality_str)
    lhs, rhs = rel.lhs, rel.rhs
    relop = RELATION_SYMBOLS.get(type(rel), str(rel.rel_op))
    normalized_expr = sp.simplify(lhs - rhs)

    try:
        poly = sp.Poly(normalized_expr, x)
        degree = poly.degree()
        coeffs = poly.all_coeffs()
    except sp.PolynomialError:
        degree = None
        coeffs = []

    discriminant = None
    roots: List[sp.Expr] = []
    domain = None
    if degree is None and (_has_radical(lhs) or _has_radical(rhs)):
        kind = "avec racine"
        try:
            domain = continuous_domain(lhs, x, sp.S.Reals).intersect(continuous_domain(rhs, x, sp.S.Reals))
        except NotImplementedError:
            domain = sp.S.Reals
    elif degree == 2:
        kind = "quadratique"
        a, b, c = coeffs
        discriminant = sp.simplify(b**2 - 4*a*c)
        if discriminant.is_real and discriminant >= 0:
            r1 = sp.simplify((-b - sp.sqrt(discriminant)) / (2*a))
            r2 = sp.simplify((-b + sp.sqrt(discriminant)) / (2*a))
            roots = sorted({r1, r2}, key=lambda s: float(s))
    elif degree == 1:
        kind = "linéaire"
    else:
        kind = "générale"

    # la résolution finale (l'ensemble solution) est toujours confiée à SymPy :
    # c'est la partie où une erreur serait la plus grave, autant s'appuyer sur
    # l'implémentation la mieux testée plutôt que de réimplémenter la logique.
    solution_set = sp.solveset(rel, x, domain=sp.S.Reals)

    return InequalityAnalysis(
        lhs=lhs, rhs=rhs, relop=relop, normalized_expr=normalized_expr,
        kind=kind, degree=degree, coefficients=coeffs,
        discriminant=discriminant, roots=roots, solution_set=solution_set,
        domain=domain,
    )
