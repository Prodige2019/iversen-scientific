"""
Moteur de résolution d'équations — même philosophie que engine/functions.py :
100% déterministe (SymPy), aucun LLM impliqué dans le calcul.

Couverture : équations linéaires (ax + b = 0), quadratiques (ax² + bx + c = 0,
avec discriminant et classification Δ>0 / Δ=0 / Δ<0), et un repli général via
sp.solve() pour les autres types (avec vérification par substitution).
"""
import re
from tokenize import TokenError
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import sympy as sp
from sympy.calculus.util import continuous_domain
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)

x = sp.symbols("x", real=True)

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,  # accepte "2x" en plus de "2*x"
    convert_xor,                          # accepte "x^2" en plus de "x**2"
)


def normalize_variable_case(expr_str: str) -> str:
    """Normalise les variables X/Y majuscules isolées vers x/y minuscules.

    SymPy est sensible à la casse (X et x sont deux symboles différents),
    mais l'utilisateur ne doit pas avoir à s'en soucier : X et x doivent
    représenter la même inconnue. On utilise un lookaround (pas \\b) car
    \\b ne détecte pas de frontière entre un chiffre et une lettre — avec
    la multiplication implicite activée (ex: "2X" valide, sans "*"), \\b
    aurait laissé passer le X de "2X" sans le convertir."""
    expr_str = re.sub(r"(?<![a-zA-Z])X(?![a-zA-Z])", "x", expr_str)
    expr_str = re.sub(r"(?<![a-zA-Z])Y(?![a-zA-Z])", "y", expr_str)
    return expr_str


def parse_math_expression(expr_str: str, local_dict: Optional[dict] = None):
    """Point d'entrée unique pour analyser une saisie utilisateur en expression
    SymPy. Plus permissif que sp.sympify seul : accepte la multiplication
    implicite ("2x", "3x(x+1)") et l'exposant "^" en plus de "**", en plus de
    la syntaxe stricte habituelle — sans changer le résultat pour une saisie
    déjà stricte (2*x**3 continue de fonctionner à l'identique)."""
    return parse_expr(expr_str, local_dict=local_dict or {}, transformations=_TRANSFORMATIONS)


@dataclass
class EquationAnalysis:
    lhs: sp.Expr
    rhs: sp.Expr
    normalized: sp.Expr          # lhs - rhs, l'équation ramenée à normalized = 0
    kind: str                    # "linéaire" | "quadratique" | "générale"
    degree: Optional[int]
    coefficients: List[sp.Expr] = field(default_factory=list)  # [a, b] ou [a, b, c] selon le degré
    discriminant: Optional[sp.Expr] = None
    solutions: List[sp.Expr] = field(default_factory=list)
    solutions_are_complete: bool = True  # False si sp.solve n'a pas trouvé de forme fermée totale
    # champs spécifiques aux équations avec radical(aux) (kind == "avec racine") :
    domain: Optional[sp.Set] = None                          # domaine de validité (existence des racines)
    rejected_solutions: List[Tuple[sp.Expr, str]] = field(default_factory=list)  # (candidate, motif du rejet)


def parse_equation(equation_str: str) -> "tuple[sp.Expr, sp.Expr]":
    """Parse une chaîne 'lhs = rhs' (ou juste 'expr', équivalent à 'expr = 0')."""
    if "=" in equation_str:
        left_str, right_str = equation_str.split("=", 1)
    else:
        left_str, right_str = equation_str, "0"
    try:
        lhs = parse_math_expression(normalize_variable_case(left_str.strip()), {"x": x})
        rhs = parse_math_expression(normalize_variable_case(right_str.strip()), {"x": x})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Équation illisible : « {equation_str} ». Détail : {e}")
    return lhs, rhs


def _has_radical(expr: sp.Expr) -> bool:
    """Détecte la présence d'un radical (racine carrée, cubique, n-ième...) portant
    sur l'inconnue x : dans SymPy, sqrt(u) et root(u, n) sont tous deux représentés
    en interne comme Pow(u, p/q) avec un exposant rationnel non entier."""
    return any(p.exp.is_Rational and p.exp.q != 1 and p.base.has(x) for p in expr.atoms(sp.Pow))


def _solve_radical_equation(lhs: sp.Expr, rhs: sp.Expr, normalized: sp.Expr) -> EquationAnalysis:
    """Équation contenant un ou plusieurs radicaux (ex: √(2x+1) = x-1).

    Méthode : le domaine de validité vient directement de continuous_domain (fiable,
    déjà utilisé pour l'étude de fonctions) ; la résolution algébrique (élévation au
    carré / à la puissance n, qui peut introduire des solutions étrangères) est
    confiée à sp.solve ; chaque candidat est ensuite systématiquement re-vérifié
    — à la fois dans le domaine ET dans l'équation d'origine (pas la version élevée
    à une puissance) — avant d'être retenu, exactement comme l'exige la méthode
    enseignée en classe."""
    try:
        domain = continuous_domain(lhs, x, sp.S.Reals).intersect(continuous_domain(rhs, x, sp.S.Reals))
    except NotImplementedError:
        domain = sp.S.Reals

    try:
        raw_candidates = sp.solve(sp.Eq(lhs, rhs), x)
        complete = True
    except NotImplementedError:
        raw_candidates = []
        complete = False

    accepted: List[sp.Expr] = []
    rejected: List[Tuple[sp.Expr, str]] = []
    for s in raw_candidates:
        if getattr(s, "is_real", None) is False:
            continue  # candidat non réel : hors périmètre (pas d'équivalent en ℝ)
        in_domain = domain.contains(s)
        if in_domain is False:
            rejected.append((s, "hors du domaine de validité (radicande négatif)"))
            continue
        try:
            checks_out = sp.simplify(lhs.subs(x, s) - rhs.subs(x, s)) == 0
        except Exception:
            checks_out = None
        if checks_out is False:
            rejected.append((s, "solution étrangère introduite par l'élévation au carré"))
            continue
        if checks_out is None:
            # simplification symbolique inconclusive : dernier recours numérique
            try:
                num = complex(lhs.subs(x, s).evalf()) - complex(rhs.subs(x, s).evalf())
                if abs(num) > 1e-9:
                    rejected.append((s, "solution étrangère introduite par l'élévation au carré"))
                    continue
            except Exception:
                pass
        accepted.append(s)

    try:
        accepted = sorted(accepted, key=lambda s: float(s))
    except (TypeError, ValueError):
        pass

    return EquationAnalysis(lhs, rhs, normalized, "avec racine", None, [],
                             solutions=accepted, solutions_are_complete=complete,
                             domain=domain, rejected_solutions=rejected)


def solve_equation(equation_str: str) -> EquationAnalysis:
    lhs, rhs = parse_equation(equation_str)
    normalized = sp.simplify(lhs - rhs)

    # tente une classification polynomiale ; si l'équation n'est pas polynomiale
    # en x (ex: contient 1/x, sqrt(x), exp(x)...), Poly lève une erreur — repli général
    try:
        poly = sp.Poly(normalized, x)
        degree = poly.degree()
        coeffs = poly.all_coeffs()  # du plus haut degré au plus bas
    except sp.PolynomialError:
        degree = None
        coeffs = []

    if degree is None and (_has_radical(lhs) or _has_radical(rhs)):
        return _solve_radical_equation(lhs, rhs, normalized)

    if degree == 1:
        kind = "linéaire"
        solutions = list(sp.solveset(sp.Eq(normalized, 0), x, domain=sp.S.Reals))
        return EquationAnalysis(lhs, rhs, normalized, kind, degree, coeffs,
                                 solutions=sorted(solutions, key=lambda s: float(s)) if all(s.is_real for s in solutions) else solutions)

    if degree == 2:
        kind = "quadratique"
        a, b, c = coeffs
        discriminant = sp.simplify(b**2 - 4*a*c)
        if discriminant.is_real and discriminant > 0:
            r1 = sp.simplify((-b - sp.sqrt(discriminant)) / (2*a))
            r2 = sp.simplify((-b + sp.sqrt(discriminant)) / (2*a))
            solutions = sorted([r1, r2], key=lambda s: float(s))
        elif discriminant.is_real and discriminant == 0:
            solutions = [sp.simplify(-b / (2*a))]
        elif discriminant.is_real and discriminant < 0:
            solutions = []  # pas de racine réelle ; le writer explique pourquoi
        else:
            # discriminant non déterminable numériquement (coefficients symboliques,
            # cas hors périmètre Phase 1) : repli sur solve() général
            solutions = list(sp.solveset(sp.Eq(normalized, 0), x, domain=sp.S.Reals))
        return EquationAnalysis(lhs, rhs, normalized, kind, degree, coeffs, discriminant, solutions)

    # repli général : sp.solve pour tout le reste (degré > 2, non polynomial, etc.)
    kind = "générale"
    try:
        raw_solutions = sp.solve(sp.Eq(normalized, 0), x)
        complete = True
    except NotImplementedError:
        raw_solutions = []
        complete = False
    real_solutions = [s for s in raw_solutions if getattr(s, "is_real", None) is not False]
    return EquationAnalysis(lhs, rhs, normalized, kind, degree, coeffs,
                             solutions=real_solutions, solutions_are_complete=complete)
