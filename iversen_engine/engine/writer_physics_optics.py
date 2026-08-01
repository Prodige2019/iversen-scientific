"""
Rédacteur pédagogique pour l'optique (lentille mince convergente).
"""
from sympy import latex
from .physics_optics import OpticsAnalysis
from .models import Correction, Step


def write_optics_correction(exercise_title, lens_label, analysis: OpticsAnalysis) -> Correction:
    correction = Correction(
        exercise_title=exercise_title, function_str=lens_label,
        subject_line=f"f' = {latex(analysis.f)}\\,cm,\\quad \\overline{{OA}} = {latex(analysis.OA)}\\,cm",
    )

    correction.add(Step(
        title="Relation de conjugaison de Descartes",
        result_latex="\\dfrac{1}{\\overline{OA'}} - \\dfrac{1}{\\overline{OA}} = \\dfrac{1}{f'}",
        explanation="Pour une lentille mince convergente, la relation de conjugaison relie la position algébrique de l'image OA', celle de l'objet OA, et la distance focale f'.",
        rule_recalled="\\dfrac{1}{\\overline{OA'}} - \\dfrac{1}{\\overline{OA}} = \\dfrac{1}{f'}",
        weight=1.5,
    ))

    correction.add(Step(
        title="Calcul de la position de l'image",
        result_latex=f"\\dfrac{{1}}{{\\overline{{OA'}}}} = \\dfrac{{1}}{{{latex(analysis.f)}}} + \\dfrac{{1}}{{{latex(analysis.OA)}}} \\quad\\Rightarrow\\quad \\overline{{OA'}} = {latex(analysis.OA_prime)}\\,cm",
        explanation="On isole 1/OA' dans la relation de conjugaison, puis on en déduit OA' en inversant.",
        weight=2.0,
    ))

    correction.add(Step(
        title="Grandissement",
        result_latex=f"\\gamma = \\dfrac{{\\overline{{OA'}}}}{{\\overline{{OA}}}} = \\dfrac{{{latex(analysis.OA_prime)}}}{{{latex(analysis.OA)}}} = {latex(analysis.magnification)}",
        explanation="Le grandissement γ compare la taille de l'image à celle de l'objet : |γ|>1 signifie une image agrandie, |γ|<1 une image réduite ; le signe donne l'orientation.",
        rule_recalled="\\gamma = \\dfrac{\\overline{OA'}}{\\overline{OA}} = \\dfrac{\\overline{A'B'}}{\\overline{AB}}",
        weight=1.5,
    ))

    real_text = "réelle (peut être projetée sur un écran)" if analysis.image_is_real else "virtuelle (ne peut pas être projetée sur un écran, observable seulement à l'œil ou avec un instrument)"
    correction.add(Step(
        title="Nature de l'image (réelle ou virtuelle)",
        result_latex=f"\\overline{{OA'}} {'> 0' if analysis.image_is_real else '< 0'} \\quad\\Rightarrow\\quad \\text{{image {real_text}}}",
        explanation="Si OA' est positif, l'image se forme après la lentille (dans le sens de propagation de la lumière) : elle est réelle. Si OA' est négatif, elle est virtuelle.",
        weight=1.5,
    ))

    orient_text = "droite (même sens que l'objet)" if analysis.image_is_upright else "renversée (sens opposé à l'objet)"
    correction.add(Step(
        title="Orientation de l'image (droite ou renversée)",
        result_latex=f"\\gamma {'> 0' if analysis.image_is_upright else '< 0'} \\quad\\Rightarrow\\quad \\text{{image {orient_text}}}",
        explanation="Le signe du grandissement γ donne l'orientation relative de l'image par rapport à l'objet.",
        weight=1.5,
    ))

    correction.compute_score()
    return correction
