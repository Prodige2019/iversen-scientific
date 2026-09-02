"""
Rédacteur pédagogique pour la résolution d'inéquations — même logique que les
autres writers de ce projet : templates conditionnels, pas de génération libre.
L'ensemble solution final vient toujours du calcul SymPy (engine/inequalities.py) ;
ce module ne fait que le mettre en mots pédagogiques.
"""
import sympy as sp
from sympy import latex
from .inequalities import InequalityAnalysis, x
from .models import Correction, Step
from .set_notation import french_set_latex as _set_to_latex


def write_inequality_correction(exercise_title: str, inequality_str: str, analysis: InequalityAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=inequality_str,
                             subject_line=f"Inéquation : {inequality_str}")

    correction.add(Step(
        title="Mise en forme normalisée",
        result_latex=f"{latex(analysis.normalized_expr)} {analysis.relop} 0",
        explanation=(
            "On ramène l'inéquation à la forme « expression {} 0 » en soustrayant le "
            "membre de droite au membre de gauche : le signe de l'inégalité entre les "
            "membres originaux ne change pas à ce stade (on ne fait que soustraire la "
            "même quantité des deux côtés)."
        ).format(analysis.relop),
        weight=1.0,
    ))

    if analysis.kind == "linéaire":
        a, b = analysis.coefficients
        flips = sp.sympify(a) < 0
        flip_note = (
            " Attention : on divise par un coefficient négatif ({}), le sens de "
            "l'inégalité est donc inversé.".format(latex(a)) if flips else
            " Le coefficient de x est positif ({}), le sens de l'inégalité est conservé.".format(latex(a))
        )
        correction.add(Step(
            title="Isolement de x",
            result_latex=f"{latex(a)}x {analysis.relop} {latex(-b)}",
            explanation="On isole le terme en x en soustrayant b des deux côtés." + flip_note,
            rule_recalled="\\text{Diviser par un nombre négatif inverse le sens de l'inégalité.}",
            weight=2.0,
        ))

    elif analysis.kind == "quadratique":
        a, b, c = analysis.coefficients
        d = analysis.discriminant
        correction.add(Step(
            title="Étude du signe du trinôme",
            result_latex=f"a = {latex(a)}, \\quad \\Delta = {latex(d)}",
            explanation=(
                "Le signe d'un trinôme ax² + bx + c dépend de son discriminant Δ et du "
                "signe de a : c'est cette étude de signe qui donne l'ensemble solution "
                "de l'inéquation, pas une résolution directe."
            ),
            rule_recalled="\\Delta = b^2 - 4ac",
            weight=2.0,
        ))
        if d is not None and d.is_real and d > 0:
            r1, r2 = analysis.roots
            sign_outside = "+" if a > 0 else "-"
            sign_inside = "-" if a > 0 else "+"
            correction.add(Step(
                title="Δ > 0 : tableau de signes",
                result_latex=(
                    f"\\text{{racines : }} x_1 = {latex(r1)}, \\ x_2 = {latex(r2)} \\quad\\Rightarrow\\quad "
                    f"\\text{{signe }} {sign_outside} \\text{{ hors }} [x_1;x_2], \\ {sign_inside} \\text{{ entre les racines}}"
                ),
                explanation=(
                    "Le trinôme a le même signe que a à l'extérieur des racines, et le "
                    "signe opposé entre les deux racines — c'est la règle du signe du "
                    "trinôme du second degré."
                ),
                rule_recalled="\\text{Signe de } ax^2+bx+c : \\text{signe de } a \\text{ à l'extérieur des racines, opposé entre elles.}",
                weight=2.0,
            ))
        elif d is not None and d.is_real and d == 0:
            r0 = sp.simplify(-b / (2*a))
            correction.add(Step(
                title="Δ = 0 : signe constant",
                result_latex=f"x_0 = {latex(r0)} \\quad\\Rightarrow\\quad \\text{{signe de }} a \\text{{ partout sauf en }} x_0",
                explanation="Le trinôme garde le signe de a sur tout ℝ, sauf en son unique racine où il s'annule.",
                weight=2.0,
            ))
        elif d is not None and d.is_real and d < 0:
            correction.add(Step(
                title="Δ < 0 : signe constant",
                result_latex="\\text{signe de } a \\text{ pour tout } x \\in \\mathbb{R}",
                explanation="Le discriminant étant négatif, le trinôme n'a pas de racine réelle et garde le signe de a sur tout ℝ.",
                weight=2.0,
            ))
    elif analysis.kind == "avec racine":
        correction.add(Step(
            title="Domaine de validité",
            result_latex=f"\\mathcal{{D}} = {_set_to_latex(analysis.domain)}",
            explanation=(
                "Une racine carrée (ou n-ième d'indice pair) n'est définie, dans ℝ, que si la "
                "quantité qu'elle contient est positive ou nulle. Toute solution de l'inéquation "
                "devra obligatoirement appartenir à cet ensemble de définition."
            ),
            rule_recalled="\\sqrt{u(x)} \\text{ est définie ssi } u(x) \\geq 0",
            weight=1.5,
        ))
        correction.add(Step(
            title="Résolution sur le domaine",
            result_latex="\\text{élévation à la puissance adaptée, avec conditions de signe}",
            explanation=(
                "On isole le radical, puis on élève les deux membres à la puissance qui l'élimine — "
                "ce qui n'est licite (sans changer le sens de l'inégalité) que sous certaines "
                "conditions de signe (par ex. « membre de droite ≥ 0 » avant d'élever au carré une "
                "racine carrée). Ces conditions sont combinées avec le domaine de validité pour "
                "obtenir l'ensemble solution final."
            ),
            weight=2.0,
        ))
    else:
        correction.add(Step(
            title="Résolution générale",
            result_latex="\\text{résolution symbolique (SymPy)}",
            explanation="L'inéquation n'est ni linéaire ni quadratique : elle est résolue par les méthodes générales de calcul formel.",
            weight=1.5,
        ))

    correction.add(Step(
        title="Ensemble des solutions",
        result_latex=f"\\mathcal{{S}} = {_set_to_latex(analysis.solution_set)}",
        explanation="On récapitule l'ensemble des valeurs de x qui vérifient l'inéquation initiale.",
        weight=1.5,
    ))

    correction.compute_score()
    return correction
