"""
Rédacteur pédagogique pour la calorimétrie (chaleur sensible / chaleur latente).
"""
from sympy import latex
from .physics_thermodynamics import ThermodynamicsAnalysis
from .models import Correction, Step


def write_thermodynamics_correction(exercise_title, label, analysis: ThermodynamicsAnalysis) -> Correction:
    if analysis.mode == "sensible":
        subject = f"m={latex(analysis.mass)}\\,g,\\ c={latex(analysis.specific_heat)}\\,J/(g \\cdot K),\\ T_i={latex(analysis.t_initial)}°C,\\ T_f={latex(analysis.t_final)}°C"
    else:
        subject = f"m={latex(analysis.mass)}\\,g,\\ L={latex(analysis.latent_heat)}\\,J/g"

    correction = Correction(exercise_title=exercise_title, function_str=label, subject_line=subject)

    if analysis.mode == "sensible":
        correction.add(Step(
            title="Formule de la chaleur sensible",
            result_latex="Q = m \\times c \\times \\Delta T \\quad \\text{avec} \\quad \\Delta T = T_f - T_i",
            explanation="Quand un corps change de température sans changer d'état, la quantité de chaleur échangée est proportionnelle à sa masse, à sa capacité thermique massique, et à la variation de température.",
            rule_recalled="Q = m\\,c\\,\\Delta T",
            weight=1.5,
        ))
        correction.add(Step(
            title="Calcul de la variation de température",
            result_latex=f"\\Delta T = T_f - T_i = {latex(analysis.t_final)} - {latex(analysis.t_initial)} = {latex(analysis.delta_t)}\\,K",
            explanation="On calcule d'abord l'écart entre température finale et initiale.",
            weight=1.5,
        ))
        correction.add(Step(
            title="Calcul de la quantité de chaleur",
            result_latex=f"Q = {latex(analysis.mass)} \\times {latex(analysis.specific_heat)} \\times {latex(analysis.delta_t)} = {latex(analysis.heat)}\\,J",
            explanation="On substitue les valeurs numériques dans la formule.",
            weight=2.0,
        ))
    else:
        correction.add(Step(
            title="Formule de la chaleur latente",
            result_latex="Q = m \\times L",
            explanation="Lors d'un changement d'état (fusion, vaporisation, ...) à température constante, la quantité de chaleur échangée est proportionnelle à la masse transformée et à la chaleur latente massique du changement d'état considéré.",
            rule_recalled="Q = m\\,L",
            weight=1.5,
        ))
        correction.add(Step(
            title="Calcul de la quantité de chaleur",
            result_latex=f"Q = {latex(analysis.mass)} \\times {latex(analysis.latent_heat)} = {latex(analysis.heat)}\\,J",
            explanation="On substitue les valeurs numériques dans la formule.",
            weight=2.0,
        ))

    sense_text = "reçue par le système (Q > 0)" if analysis.is_absorbed else "cédée par le système (Q < 0)"
    correction.add(Step(
        title="Sens du transfert thermique",
        result_latex=f"Q {'> 0' if analysis.is_absorbed else '< 0'} \\quad\\Rightarrow\\quad \\text{{chaleur {sense_text}}}",
        explanation="Le signe de Q indique le sens de l'échange thermique : positif si le système reçoit de la chaleur (il se réchauffe ou change d'état en absorbant), négatif s'il en cède (il se refroidit ou change d'état en libérant).",
        rule_recalled="Q > 0 : \\text{chaleur reçue} \\qquad Q < 0 : \\text{chaleur cédée}",
        weight=1.0,
    ))

    correction.compute_score()
    return correction
