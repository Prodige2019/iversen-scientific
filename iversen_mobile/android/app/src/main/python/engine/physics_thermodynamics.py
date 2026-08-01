"""
Moteur de calorimétrie — quantité de chaleur échangée, soit par variation de
température (chaleur sensible, Q = m·c·ΔT), soit lors d'un changement d'état
(chaleur latente, Q = m·L). Calcul exact via SymPy, même philosophie que le
reste du projet.
"""
from dataclasses import dataclass
from typing import Optional
import sympy as sp
from .equations import parse_math_expression


def _parse_value(value_str: str, label: str) -> sp.Expr:
    try:
        return sp.nsimplify(parse_math_expression(value_str))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Valeur illisible pour {label} : « {value_str} ». Détail : {e}")


@dataclass
class ThermodynamicsAnalysis:
    mode: str
    mass: sp.Expr
    heat: sp.Expr
    specific_heat: Optional[sp.Expr] = None
    t_initial: Optional[sp.Expr] = None
    t_final: Optional[sp.Expr] = None
    delta_t: Optional[sp.Expr] = None
    latent_heat: Optional[sp.Expr] = None
    is_absorbed: bool = True


def analyze_sensible_heat(mass_str: str, specific_heat_str: str, t_initial_str: str, t_final_str: str) -> ThermodynamicsAnalysis:
    m = _parse_value(mass_str, "m")
    c = _parse_value(specific_heat_str, "c")
    t1 = _parse_value(t_initial_str, "T_initiale")
    t2 = _parse_value(t_final_str, "T_finale")

    if m <= 0:
        raise ValueError(f"La masse doit être strictement positive (reçu : {m}).")
    if c <= 0:
        raise ValueError(f"La capacité thermique massique doit être strictement positive (reçu : {c}).")

    delta_t = sp.simplify(t2 - t1)
    q = sp.simplify(m * c * delta_t)

    return ThermodynamicsAnalysis(
        mode="sensible", mass=m, specific_heat=c, t_initial=t1, t_final=t2,
        delta_t=delta_t, heat=q, is_absorbed=bool(q >= 0),
    )


def analyze_latent_heat(mass_str: str, latent_heat_str: str) -> ThermodynamicsAnalysis:
    m = _parse_value(mass_str, "m")
    L = _parse_value(latent_heat_str, "L")

    if m <= 0:
        raise ValueError(f"La masse doit être strictement positive (reçu : {m}).")
    if L == 0:
        raise ValueError("La chaleur latente ne peut pas être nulle.")

    q = sp.simplify(m * L)
    return ThermodynamicsAnalysis(
        mode="latente", mass=m, latent_heat=L, heat=q, is_absorbed=bool(q >= 0),
    )
