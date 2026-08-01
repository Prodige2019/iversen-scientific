"""
Moteur de cinématique — mouvement rectiligne uniformément varié (MRUV).
Étant donné x0, v0, a et t, calcule x(t), v(t), et si le mobile décélère
(a et v0 de signes opposés), le temps et la distance jusqu'à l'arrêt (v=0).

Calcul exact via SymPy, même philosophie que le reste du projet.
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
class KinematicsAnalysis:
    x0: sp.Expr
    v0: sp.Expr
    a: sp.Expr
    t_value: sp.Expr
    position_at_t: sp.Expr
    velocity_at_t: sp.Expr
    is_decelerating: bool
    stop_time: Optional[sp.Expr] = None
    stop_distance: Optional[sp.Expr] = None


def analyze_kinematics(x0_str: str, v0_str: str, a_str: str, t_str: str) -> KinematicsAnalysis:
    x0 = _parse_value(x0_str, "x0")
    v0 = _parse_value(v0_str, "v0")
    a = _parse_value(a_str, "a")
    t_value = _parse_value(t_str, "t")

    if not t_value.is_real or t_value < 0:
        raise ValueError(f"Le temps t doit être positif ou nul (reçu : {t_value}).")

    position_at_t = sp.simplify(x0 + v0 * t_value + sp.Rational(1, 2) * a * t_value**2)
    velocity_at_t = sp.simplify(v0 + a * t_value)

    is_decelerating = bool(a != 0 and v0 != 0 and sp.sign(a) != sp.sign(v0))

    stop_time = None
    stop_distance = None
    if is_decelerating:
        stop_time = sp.simplify(-v0 / a)
        stop_distance = sp.simplify(x0 + v0 * stop_time + sp.Rational(1, 2) * a * stop_time**2)

    return KinematicsAnalysis(
        x0=x0, v0=v0, a=a, t_value=t_value,
        position_at_t=position_at_t, velocity_at_t=velocity_at_t,
        is_decelerating=is_decelerating, stop_time=stop_time, stop_distance=stop_distance,
    )
