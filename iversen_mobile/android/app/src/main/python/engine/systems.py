"""
Moteur de résolution de systèmes de 2 équations linéaires à 2 inconnues (x, y) —
même philosophie que le reste du projet : la méthode de substitution est reconstruite
pas à pas pour la pédagogie, mais l'ensemble solution final vient toujours de
sp.linsolve() (SymPy), qui gère nativement les 3 cas (solution unique, aucune solution,
infinité de solutions) de façon fiable.
"""
from tokenize import TokenError
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import sympy as sp
from .equations import normalize_variable_case, parse_math_expression

x, y = sp.symbols("x y", real=True)


@dataclass
class SystemAnalysis:
    eq1: sp.Eq
    eq2: sp.Eq
    kind: str                          # "unique" | "aucune" | "infinité"
    substitution_variable: Optional[sp.Symbol] = None   # variable isolée en premier (x ou y)
    substitution_expr: Optional[sp.Expr] = None         # son expression en fonction de l'autre
    other_variable: Optional[sp.Symbol] = None
    other_value: Optional[sp.Expr] = None                # valeur numérique trouvée pour l'autre variable
    substitution_value: Optional[sp.Expr] = None         # valeur numérique déduite pour la variable isolée
    general_solution: Optional[str] = None               # description textuelle si infinité de solutions


def _parse_linear_equation(equation_str: str, label: str) -> sp.Eq:
    if "=" not in equation_str:
        raise ValueError(f"L'équation {label} doit contenir un « = » (reçu : « {equation_str} »).")
    left_str, right_str = equation_str.split("=", 1)
    try:
        lhs = parse_math_expression(normalize_variable_case(left_str.strip()), {"x": x, "y": y})
        rhs = parse_math_expression(normalize_variable_case(right_str.strip()), {"x": x, "y": y})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Équation {label} illisible : « {equation_str} ». Détail : {e}")
    expr = lhs - rhs
    if not expr.free_symbols <= {x, y}:
        raise ValueError(
            f"L'équation {label} doit porter uniquement sur x et y (reçu : « {equation_str} »)."
        )
    try:
        poly = sp.Poly(expr, x, y)
        if poly.total_degree() > 1:
            raise ValueError(f"L'équation {label} n'est pas linéaire (reçu : « {equation_str} »).")
    except sp.PolynomialError:
        raise ValueError(f"L'équation {label} n'est pas polynomiale en x, y (reçu : « {equation_str} »).")
    return sp.Eq(lhs, rhs)


def parse_system(equation1_str: str, equation2_str: str) -> Tuple[sp.Eq, sp.Eq]:
    eq1 = _parse_linear_equation(equation1_str, "1")
    eq2 = _parse_linear_equation(equation2_str, "2")
    return eq1, eq2


def solve_system(equation1_str: str, equation2_str: str) -> SystemAnalysis:
    eq1, eq2 = parse_system(equation1_str, equation2_str)

    # source de vérité pour le résultat final : sp.linsolve
    solution_set = sp.linsolve([eq1, eq2], [x, y])

    if solution_set == sp.S.EmptySet:
        return SystemAnalysis(eq1=eq1, eq2=eq2, kind="aucune")

    (sol_x, sol_y), = solution_set
    if sol_x.free_symbols or sol_y.free_symbols:
        # infinité de solutions : système dégénéré (les deux équations décrivent la même droite)
        if sol_x.free_symbols and not sol_y.free_symbols:
            general = f"x = {sp.latex(sol_x)}, \\ y = {sp.latex(sol_y)} \\text{{ (libre)}}"
        elif sol_y.free_symbols and not sol_x.free_symbols:
            general = f"x = {sp.latex(sol_x)} \\text{{ (libre)}}, \\ y = {sp.latex(sol_y)}"
        else:
            # le paramètre libre est l'une des deux inconnues elles-mêmes (cas le plus
            # courant : sol_y = y) — on l'affiche comme un paramètre t plutôt que "y = y"
            free_sym = next(iter(sol_x.free_symbols | sol_y.free_symbols))
            general = f"x = {sp.latex(sol_x.subs(free_sym, sp.Symbol('t')))}, \\ y = {sp.latex(sol_y.subs(free_sym, sp.Symbol('t')))}, \\ t \\in \\mathbb{{R}}"
        return SystemAnalysis(eq1=eq1, eq2=eq2, kind="infinité", general_solution=general)

    # reconstruction pédagogique de la méthode de substitution, cohérente avec le
    # résultat déjà connu (sol_x, sol_y) : on choisit d'isoler y depuis eq1 si possible
    # (coefficient non nul), sinon x depuis eq1, pour présenter une démarche naturelle.
    coeff_y_eq1 = eq1.lhs.coeff(y) - eq1.rhs.coeff(y)
    if coeff_y_eq1 != 0:
        sub_var, other_var = y, x
        sub_expr = sp.solve(eq1, y)[0]
    else:
        sub_var, other_var = x, y
        sub_expr = sp.solve(eq1, x)[0]

    other_value = sol_x if other_var == x else sol_y
    sub_value = sol_y if sub_var == y else sol_x

    return SystemAnalysis(
        eq1=eq1, eq2=eq2, kind="unique",
        substitution_variable=sub_var, substitution_expr=sub_expr,
        other_variable=other_var, other_value=other_value,
        substitution_value=sub_value,
    )
