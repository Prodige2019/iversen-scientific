"""
Moteur d'étude de suites définies par récurrence u_{n+1} = f(u_n), u_{n0} = u0.

Convention d'entrée : la récurrence est donnée comme une expression SymPy en la
variable `u` (représentant u_n), par exemple :
  - "u + 3"     → u_{n+1} = u_n + 3   (arithmétique, raison r = 3)
  - "2*u"       → u_{n+1} = 2 u_n     (géométrique, raison q = 2)
  - "2*u + 3"   → u_{n+1} = 2 u_n + 3 (arithmético-géométrique)
  - "u**2 - 1"  → récurrence non affine, pas de forme fermée automatique

Comme pour le reste du projet : classification déterministe (SymPy), pas de LLM.
"""
from dataclasses import dataclass, field
from tokenize import TokenError
from typing import List, Optional
import sympy as sp
from .equations import parse_math_expression

u = sp.symbols("u", real=True)
n = sp.symbols("n", integer=True, nonnegative=True)


@dataclass
class SequenceAnalysis:
    first_term: sp.Expr
    start_index: int
    recurrence_rhs: sp.Expr        # f(u), tel que u_{n+1} = f(u_n)
    kind: str                      # "arithmétique" | "géométrique" | "arithmético-géométrique" | "non reconnue"
    a: Optional[sp.Expr] = None    # coefficient multiplicatif (pente de l'affine f(u) = a*u + b)
    b: Optional[sp.Expr] = None    # coefficient additif
    common_difference: Optional[sp.Expr] = None   # r, si arithmétique
    common_ratio: Optional[sp.Expr] = None        # q, si géométrique ou arithmético-géométrique
    fixed_point: Optional[sp.Expr] = None          # L, si arithmético-géométrique (u_n - L est géométrique)
    general_term: Optional[sp.Expr] = None         # u_n en fonction de n, forme fermée si trouvée
    monotonicity: Optional[str] = None             # "croissante" | "décroissante" | "constante" | "alternée" | None
    limit: Optional[sp.Expr] = None                # limite quand n → +∞ (peut être sp.oo, -sp.oo, ou None si pas de limite)
    limit_exists: bool = True
    first_terms: List[sp.Expr] = field(default_factory=list)  # quelques termes numériques, toujours calculés


def parse_recurrence(recurrence_str: str) -> sp.Expr:
    try:
        return parse_math_expression(recurrence_str.strip(), {"u": u})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Récurrence illisible : « {recurrence_str} ». Détail : {e}")


def analyze_sequence(first_term_str: str, recurrence_str: str, start_index: int = 0,
                      num_terms: int = 6) -> SequenceAnalysis:
    try:
        u0 = parse_math_expression(first_term_str.strip())
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Premier terme illisible : « {first_term_str} ». Détail : {e}")

    f_u = parse_recurrence(recurrence_str)

    # quelques termes numériques : toujours calculables, quelle que soit la forme de f
    terms = [u0]
    for _ in range(num_terms - 1):
        terms.append(sp.simplify(f_u.subs(u, terms[-1])))

    # classification : f(u) est-elle affine en u ? (a*u + b)
    try:
        poly = sp.Poly(f_u, u)
        is_affine = poly.degree() <= 1
    except sp.PolynomialError:
        is_affine = False

    if not is_affine:
        return SequenceAnalysis(
            first_term=u0, start_index=start_index, recurrence_rhs=f_u,
            kind="non reconnue", first_terms=terms,
        )

    a_coeff = sp.simplify(f_u.diff(u))          # pente
    b_coeff = sp.simplify(f_u - a_coeff * u)     # ordonnée à l'origine

    k = n - start_index  # nombre de pas depuis le premier terme

    if a_coeff == 1 and b_coeff == 0:
        # u_{n+1} = u_n : suite constante (cas particulier dégénéré)
        kind = "arithmétique"
        r = sp.Integer(0)
        general_term = u0
        monotonicity = "constante"
        limit, limit_exists = u0, True

    elif a_coeff == 1:
        kind = "arithmétique"
        r = b_coeff
        general_term = u0 + k * r
        if r > 0:
            monotonicity, limit, limit_exists = "croissante", sp.oo, True
        elif r < 0:
            monotonicity, limit, limit_exists = "décroissante", -sp.oo, True
        else:
            monotonicity, limit, limit_exists = "constante", u0, True

    elif b_coeff == 0:
        kind = "géométrique"
        r = None
        q = a_coeff
        general_term = u0 * q**k
        limit_exists = True
        if q == 1:
            monotonicity, limit = "constante", u0
        elif -1 < q < 1:
            monotonicity = "décroissante" if (u0 > 0 and q >= 0) else ("croissante" if (u0 < 0 and q >= 0) else "non monotone (signe alterné)")
            limit = sp.Integer(0)
        elif q > 1:
            monotonicity = "croissante" if u0 > 0 else ("décroissante" if u0 < 0 else "constante")
            limit = sp.oo if u0 > 0 else (-sp.oo if u0 < 0 else sp.Integer(0))
        else:  # q <= -1
            monotonicity, limit, limit_exists = "non monotone (signe alterné)", None, False

    else:
        kind = "arithmético-géométrique"
        r = None
        q = a_coeff
        fixed_point = sp.simplify(b_coeff / (1 - a_coeff))
        general_term = sp.simplify(fixed_point + (u0 - fixed_point) * q**k)
        limit_exists = True
        if q == 1:
            monotonicity, limit = "constante", u0
        elif -1 < q < 1:
            monotonicity = None  # dépend du signe de (u0 - L), pas généralisable simplement
            limit = fixed_point
        elif q > 1:
            monotonicity = None
            diff0 = u0 - fixed_point
            limit = sp.oo if diff0 > 0 else (-sp.oo if diff0 < 0 else fixed_point)
        else:
            monotonicity, limit, limit_exists = "non monotone (signe alterné)", None, False

    result = SequenceAnalysis(
        first_term=u0, start_index=start_index, recurrence_rhs=f_u, kind=kind,
        a=a_coeff, b=b_coeff, first_terms=terms, general_term=general_term,
        monotonicity=monotonicity, limit=limit, limit_exists=limit_exists,
    )
    if kind == "arithmétique":
        result.common_difference = r
    elif kind == "géométrique":
        result.common_ratio = a_coeff
    elif kind == "arithmético-géométrique":
        result.common_ratio = a_coeff
        result.fixed_point = fixed_point
    return result
