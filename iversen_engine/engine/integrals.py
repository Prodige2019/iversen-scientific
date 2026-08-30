"""
Moteur de calcul intégral : primitives (intégrale indéfinie) et intégrale
définie (aire algébrique entre a et b) pour une fonction f(x).
"""
from dataclasses import dataclass
from typing import Optional
import sympy as sp
from sympy import S, Interval
from sympy.calculus.util import continuous_domain
from .equations import x, normalize_variable_case, parse_math_expression


@dataclass
class IntegralAnalysis:
    function: sp.Expr
    primitive: sp.Expr
    is_definite: bool
    a: Optional[sp.Expr] = None
    b: Optional[sp.Expr] = None
    value: Optional[sp.Expr] = None


def analyze_integral(function_str: str, a_str: Optional[str] = None, b_str: Optional[str] = None) -> IntegralAnalysis:
    try:
        f = parse_math_expression(normalize_variable_case(function_str), {"x": x})
    except (sp.SympifyError, TypeError, SyntaxError) as e:
        raise ValueError(f"Fonction illisible : « {function_str} ». Détail : {e}")

    try:
        primitive = sp.integrate(f, x)
    except Exception as e:
        raise ValueError(f"Impossible de calculer une primitive de cette fonction : {e}")

    if isinstance(primitive, sp.Integral) or primitive.has(sp.Integral):
        raise ValueError(
            "Cette fonction n'admet pas de primitive exprimable avec les "
            "fonctions usuelles (pas de forme fermée connue)."
        )

    is_definite = a_str is not None and b_str is not None and a_str != "" and b_str != ""
    a_val = b_val = value = None
    if is_definite:
        try:
            a_val = parse_math_expression(normalize_variable_case(a_str), {"x": x})
            b_val = parse_math_expression(normalize_variable_case(b_str), {"x": x})
        except (sp.SympifyError, TypeError, SyntaxError) as e:
            raise ValueError(f"Bornes illisibles. Détail : {e}")

        # Garde-fou essentiel : le théorème fondamental de l'analyse ne
        # s'applique que si f est continue (donc définie) sur TOUT le segment
        # [a, b]. Sans ce contrôle, appliquer F(b) - F(a) sur une fonction qui
        # a une discontinuité entre a et b (ex: 1/x entre -1 et 1) produit un
        # résultat sans aucun sens mathématique (ex: un nombre complexe pour
        # une "aire" réelle) et induirait l'élève en erreur.
        try:
            lo, hi = sp.Min(a_val, b_val), sp.Max(a_val, b_val)
            domain = continuous_domain(f, x, S.Reals)
            if not Interval(lo, hi).is_subset(domain):
                raise ValueError(
                    "f n'est pas continue sur tout le segment "
                    f"[{sp.nsimplify(lo)} ; {sp.nsimplify(hi)}] (elle n'y est même "
                    "pas toujours définie) : le théorème fondamental de l'analyse "
                    "ne s'applique pas directement ici. Il s'agirait d'une "
                    "intégrale impropre, dont l'étude de convergence dépasse ce "
                    "module."
                )
        except ValueError:
            raise
        except Exception:
            # Le test de continuité peut échouer sur des bornes/fonctions trop
            # exotiques (paramètres symboliques...) ; dans ce cas on ne bloque
            # pas inutilement un calcul par ailleurs valide.
            pass

        try:
            value = sp.simplify(primitive.subs(x, b_val) - primitive.subs(x, a_val))
        except Exception as e:
            raise ValueError(f"Calcul de l'intégrale définie impossible : {e}")

    return IntegralAnalysis(
        function=f, primitive=primitive, is_definite=is_definite,
        a=a_val, b=b_val, value=value,
    )
