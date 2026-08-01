"""
Rédacteur pédagogique pour la cinématique (MRUV).
"""
import sympy as sp
from sympy import latex
from .physics_kinematics import KinematicsAnalysis
from .models import Correction, Step


def write_kinematics_correction(exercise_title, motion_label, analysis: KinematicsAnalysis) -> Correction:
    correction = Correction(
        exercise_title=exercise_title, function_str=motion_label,
        subject_line=f"x_0={latex(analysis.x0)}\\,m,\\ v_0={latex(analysis.v0)}\\,m/s,\\ a={latex(analysis.a)}\\,m/s^2,\\ t={latex(analysis.t_value)}\\,s",
    )

    correction.add(Step(
        title="Équations horaires du MRUV",
        result_latex="x(t) = x_0 + v_0 t + \\dfrac{1}{2}at^2 \\qquad v(t) = v_0 + at",
        explanation="Pour un mouvement rectiligne uniformément varié (accélération a constante), la position et la vitesse à l'instant t se déduisent directement des conditions initiales.",
        rule_recalled="x(t) = x_0 + v_0 t + \\tfrac{1}{2}at^2 \\qquad v(t) = v_0 + at",
        weight=1.0,
    ))

    correction.add(Step(
        title=f"Position à t = {latex(analysis.t_value)} s",
        result_latex=f"x({latex(analysis.t_value)}) = {latex(analysis.x0)} + {latex(analysis.v0)} \\times {latex(analysis.t_value)} + \\dfrac{{1}}{{2}} \\times {latex(analysis.a)} \\times {latex(analysis.t_value)}^2 = {latex(analysis.position_at_t)}\\,m",
        explanation="On substitue les valeurs numériques dans l'équation horaire de la position.",
        weight=2.0,
    ))

    correction.add(Step(
        title=f"Vitesse à t = {latex(analysis.t_value)} s",
        result_latex=f"v({latex(analysis.t_value)}) = {latex(analysis.v0)} + {latex(analysis.a)} \\times {latex(analysis.t_value)} = {latex(analysis.velocity_at_t)}\\,m/s",
        explanation="On substitue les valeurs numériques dans l'équation horaire de la vitesse.",
        weight=2.0,
    ))

    if analysis.is_decelerating:
        correction.add(Step(
            title="Décélération détectée : temps et distance d'arrêt",
            result_latex=f"v(t)=0 \\ \\Rightarrow\\ t_{{arrêt}} = -\\dfrac{{v_0}}{{a}} = {latex(analysis.stop_time)}\\,s \\qquad x(t_{{arrêt}}) = {latex(analysis.stop_distance)}\\,m",
            explanation=(
                "L'accélération et la vitesse initiale étant de signes opposés, le mobile "
                "ralentit : on calcule l'instant où sa vitesse s'annule, puis la distance "
                "parcourue jusqu'à cet instant (distance de freinage)."
            ),
            rule_recalled="v(t)=0 \\iff t = -\\dfrac{v_0}{a}",
            weight=2.0,
        ))
    else:
        correction.add(Step(
            title="Nature du mouvement",
            result_latex="\\text{pas de décélération (a et } v_0 \\text{ de même sens, ou l'un des deux est nul)}",
            explanation="Le mobile accélère ou se déplace à vitesse constante ; il n'y a pas d'arrêt à calculer dans ce cadre.",
            weight=1.0,
        ))

    if analysis.a != 0:
        lhs = analysis.velocity_at_t**2 - analysis.v0**2
        rhs = 2 * analysis.a * (analysis.position_at_t - analysis.x0)
        check = sp.simplify(lhs - rhs)
        correction.add(Step(
            title="Vérification (relation indépendante du temps)",
            result_latex=f"v(t)^2 - v_0^2 - 2a(x(t)-x_0) = {latex(check)}",
            explanation="Cette relation ne fait pas intervenir t explicitement : elle doit toujours être vérifiée, c'est un garde-fou de cohérence contre une erreur de calcul.",
            rule_recalled="v^2 = v_0^2 + 2a(x - x_0)",
            weight=1.5,
        ))

    correction.compute_score()
    return correction
