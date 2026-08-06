"""
Moteur de résolution de systèmes d'équations linéaires à n inconnues
(x, y, z, t) — généralisé : supporte 2, 3, 4 équations (et inconnues),
pas seulement le cas x/y à 2 équations d'avant.

La méthode utilisée est la même philosophie que le reste du projet :
sp.linsolve() est la source de vérité pour le résultat (gère nativement
les 3 cas : solution unique, aucune solution, infinité de solutions),
avec une reconstruction pédagogique des étapes autour.
"""
from tokenize import TokenError
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import sympy as sp
from .equations import normalize_variable_case, parse_math_expression

# Jeu de variables reconnues, dans l'ordre d'introduction habituel en
# mathématiques francophones. Au-delà de 4 inconnues, ce n'est plus un
# exercice de lycée — x, y, z, t couvrent tout le programme de Terminale.
_VARIABLE_NAMES = ["x", "y", "z", "t"]
_ALL_SYMBOLS = {name: sp.symbols(name, real=True) for name in _VARIABLE_NAMES}


@dataclass
class SystemAnalysis:
    equations: List[sp.Eq]
    variables: List[sp.Symbol]
    kind: str                                            # "unique" | "aucune" | "infinité"
    solution: Optional[Dict[sp.Symbol, sp.Expr]] = None   # rempli si kind == "unique"
    general_solution: Optional[str] = None                # rempli si kind == "infinité"


def _parse_linear_equation(equation_str: str, label: str) -> sp.Eq:
    if "=" not in equation_str:
        raise ValueError(f"L'équation {label} doit contenir un « = » (reçu : « {equation_str} »).")
    left_str, right_str = equation_str.split("=", 1)
    try:
        lhs = parse_math_expression(normalize_variable_case(left_str.strip()), _ALL_SYMBOLS)
        rhs = parse_math_expression(normalize_variable_case(right_str.strip()), _ALL_SYMBOLS)
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Équation {label} illisible : « {equation_str} ». Détail : {e}")
    return sp.Eq(lhs, rhs)


def parse_system(equation_strs: List[str]):
    if len(equation_strs) < 2:
        raise ValueError("Un système doit contenir au moins 2 équations.")

    equations = [_parse_linear_equation(s, str(i)) for i, s in enumerate(equation_strs, start=1)]

    used_symbols = set()
    for eq in equations:
        used_symbols |= (eq.lhs - eq.rhs).free_symbols

    unsupported = used_symbols - set(_ALL_SYMBOLS.values())
    if unsupported:
        names = ", ".join(sorted(str(s) for s in unsupported))
        raise ValueError(f"Variable(s) non reconnue(s) : {names}. Seules x, y, z, t sont supportées.")

    variables = [_ALL_SYMBOLS[name] for name in _VARIABLE_NAMES if _ALL_SYMBOLS[name] in used_symbols]
    if not variables:
        raise ValueError("Aucune inconnue détectée dans ce système.")

    for i, eq in enumerate(equations, start=1):
        expr = eq.lhs - eq.rhs
        try:
            poly = sp.Poly(expr, *variables)
            if poly.total_degree() > 1:
                raise ValueError(f"L'équation {i} n'est pas linéaire (reçu : « {equation_strs[i-1]} »).")
        except sp.PolynomialError:
            raise ValueError(
                f"L'équation {i} n'est pas polynomiale en {', '.join(str(v) for v in variables)}."
            )

    return equations, variables


def solve_system(equation_strs: List[str]) -> SystemAnalysis:
    equations, variables = parse_system(equation_strs)

    solution_set = sp.linsolve(equations, variables)

    if solution_set == sp.S.EmptySet:
        return SystemAnalysis(equations=equations, variables=variables, kind="aucune")

    (solution_tuple,) = solution_set
    has_free = any(val.free_symbols for val in solution_tuple)

    if has_free:
        parts = []
        for var, val in zip(variables, solution_tuple):
            if val == var:
                parts.append(f"{sp.latex(var)} \\ \\text{{libre}}")
            else:
                parts.append(f"{sp.latex(var)} = {sp.latex(val)}")
        general = ", \\ ".join(parts)
        return SystemAnalysis(equations=equations, variables=variables, kind="infinité", general_solution=general)

    solution = dict(zip(variables, solution_tuple))
    return SystemAnalysis(equations=equations, variables=variables, kind="unique", solution=solution)
