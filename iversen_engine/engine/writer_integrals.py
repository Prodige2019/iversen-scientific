"""
Rédacteur pédagogique pour le calcul de primitives et d'intégrales définies.
"""
import sympy as sp
from .integrals import IntegralAnalysis, x
from .models import Correction, Step


def write_integral_correction(exercise_title: str, function_str: str, analysis: IntegralAnalysis) -> Correction:
    if analysis.is_definite:
        subject = f"\\int_{{{sp.latex(analysis.a)}}}^{{{sp.latex(analysis.b)}}} {function_str}\\,dx"
    else:
        subject = f"\\int {function_str}\\,dx"
    correction = Correction(exercise_title=exercise_title, function_str=function_str, subject_line=subject)

    correction.add(Step(
        title="Fonction à intégrer",
        result_latex=f"f(x) = {sp.latex(analysis.function)}",
        explanation=(
            "On identifie la fonction dont on cherche une primitive (ou "
            "l'aire algébrique sous la courbe, si des bornes sont données)."
        ),
        weight=1.0,
    ))

    correction.add(Step(
        title="Calcul d'une primitive",
        result_latex=f"F(x) = {sp.latex(analysis.primitive)} + C",
        explanation=(
            "On cherche une fonction F telle que F'(x) = f(x), en utilisant "
            "les primitives usuelles (puissances, exponentielle, logarithme, "
            "fonctions trigonométriques...) et les règles de linéarité. La "
            "constante C est arbitraire : F n'est définie qu'à une constante "
            "additive près."
        ),
        rule_recalled="\\text{Deux primitives d'une même fonction diffèrent toujours d'une constante.}",
        weight=2.5,
    ))

    if analysis.is_definite:
        fb = analysis.primitive.subs(x, analysis.b)
        fa = analysis.primitive.subs(x, analysis.a)
        correction.add(Step(
            title="Application du théorème fondamental de l'analyse",
            result_latex=(
                f"\\int_{{{sp.latex(analysis.a)}}}^{{{sp.latex(analysis.b)}}} f(x)\\,dx "
                f"= F({sp.latex(analysis.b)}) - F({sp.latex(analysis.a)}) "
                f"= {sp.latex(fb)} - \\left( {sp.latex(fa)} \\right)"
            ),
            explanation=(
                "Pour une intégrale définie entre a et b, on évalue une "
                "primitive F en b, on lui soustrait sa valeur en a — le choix "
                "de la constante C n'a aucune importance ici, elle s'annule "
                "dans la soustraction."
            ),
            rule_recalled="\\int_a^b f(x)\\,dx = F(b) - F(a)",
            weight=2.0,
        ))
        correction.add(Step(
            title="Résultat",
            result_latex=(
                f"\\int_{{{sp.latex(analysis.a)}}}^{{{sp.latex(analysis.b)}}} "
                f"f(x)\\,dx = {sp.latex(analysis.value)}"
            ),
            explanation=(
                "Cette valeur représente l'aire algébrique entre la courbe de "
                "f et l'axe des abscisses sur [a, b] — négative si la courbe "
                "est sous l'axe sur cette portion."
            ),
            weight=1.5,
        ))

    correction.compute_score()
    return correction
