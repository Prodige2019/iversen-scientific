"""
Rédacteur pédagogique pour l'étude d'un nombre complexe.
"""
import sympy as sp
from sympy import latex
from .complex_numbers import ComplexAnalysis
from .models import Correction, Step


def write_complex_correction(exercise_title, z_str, analysis: ComplexAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=z_str,
                             subject_line=f"z = {z_str}")

    correction.add(Step(
        title="Forme algébrique",
        result_latex=f"z = {latex(analysis.re)} + {latex(analysis.im)}\\,i \\qquad \\text{{Re}}(z) = {latex(analysis.re)}, \\ \\text{{Im}}(z) = {latex(analysis.im)}",
        explanation="On identifie la partie réelle et la partie imaginaire de z, écrit sous forme algébrique a + bi.",
        weight=1.0,
    ))

    correction.add(Step(
        title="Calcul du module",
        result_latex=f"|z| = \\sqrt{{\\text{{Re}}(z)^2 + \\text{{Im}}(z)^2}} = {latex(analysis.modulus)}",
        explanation="Le module de z mesure sa distance à l'origine dans le plan complexe.",
        rule_recalled="|a+bi| = \\sqrt{a^2+b^2}",
        weight=2.0,
    ))

    arg_note = (
        "C'est un angle remarquable du cercle trigonométrique."
        if analysis.argument_is_notable else
        "Cet angle n'est pas un angle remarquable usuel ; on le laisse sous forme d'arctangente/valeur exacte."
    )
    correction.add(Step(
        title="Calcul de l'argument",
        result_latex=f"\\arg(z) = {latex(analysis.argument)}",
        explanation=f"L'argument de z est l'angle formé avec l'axe des réels positifs, déterminé à partir du signe de Re(z) et Im(z) pour se placer dans le bon quadrant. {arg_note}",
        weight=2.0,
    ))

    correction.add(Step(
        title="Forme trigonométrique",
        result_latex=f"z = {analysis.trig_form}",
        explanation="On réécrit z à partir de son module et de son argument : c'est la forme trigonométrique.",
        rule_recalled="z = |z|\\left(\\cos(\\arg z) + i\\sin(\\arg z)\\right)",
        weight=1.5,
    ))

    correction.add(Step(
        title="Forme exponentielle",
        result_latex=f"z = {analysis.exp_form}",
        explanation="La notation exponentielle (notation d'Euler) est une écriture condensée équivalente à la forme trigonométrique.",
        rule_recalled="z = |z|\\,e^{i\\arg z}",
        weight=1.5,
    ))

    correction.add(Step(
        title="Conjugué",
        result_latex=f"\\bar{{z}} = {latex(analysis.conjugate)}",
        explanation="Le conjugué de z s'obtient en changeant le signe de la partie imaginaire.",
        rule_recalled="\\overline{a+bi} = a - bi",
        weight=1.0,
    ))

    check = sp.simplify(analysis.z * analysis.conjugate - analysis.modulus**2)
    correction.add(Step(
        title="Vérification : z × z̄ = |z|²",
        result_latex=f"z \\times \\bar{{z}} = {latex(sp.simplify(analysis.z * analysis.conjugate))} = |z|^2 \\quad (\\text{{écart}} : {latex(check)})",
        explanation="Une propriété fondamentale du produit d'un nombre complexe par son conjugué sert de garde-fou : elle doit toujours redonner le carré du module.",
        weight=1.0,
    ))

    correction.compute_score()
    return correction
