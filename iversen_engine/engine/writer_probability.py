"""
Rédacteur pédagogique pour la loi binomiale B(n, p).
"""
import sympy as sp
from sympy import latex
from .probability import BinomialAnalysis
from .models import Correction, Step


def write_binomial_correction(exercise_title, n, p_str, k, analysis: BinomialAnalysis) -> Correction:
    subject = f"X \\sim \\mathcal{{B}}({n} \\, ; \\, {p_str})"
    correction = Correction(exercise_title=exercise_title, function_str=f"B({n}, {p_str})",
                             subject_line=f"Loi binomiale : ${subject}$")

    correction.add(Step(
        title="Identification du schéma de Bernoulli",
        result_latex=f"X \\sim \\mathcal{{B}}(n={n} \\, ; \\, p={latex(analysis.p)})",
        explanation=(
            "On répète n épreuves de Bernoulli identiques et indépendantes, chacune avec "
            "une probabilité de succès p : le nombre X de succès obtenus suit alors une "
            "loi binomiale de paramètres n et p."
        ),
        rule_recalled="X \\sim \\mathcal{B}(n,p) \\iff P(X=k) = \\binom{n}{k} p^k (1-p)^{n-k}",
        weight=1.5,
    ))

    if k is not None:
        correction.add(Step(
            title=f"Calcul de P(X = {k})",
            result_latex=f"P(X={k}) = \\binom{{{n}}}{{{k}}} \\, {latex(analysis.p)}^{{{k}}} (1-{latex(analysis.p)})^{{{n-k}}} = {latex(analysis.proba_exact)} \\approx {analysis.proba_exact_decimal:.4f}",
            explanation=(
                f"On applique directement la formule de la loi binomiale avec k={k} : "
                f"le coefficient binomial compte le nombre de façons d'obtenir {k} succès "
                f"parmi {n} épreuves, et le reste du produit donne la probabilité d'une "
                f"séquence précise avec exactement {k} succès."
            ),
            weight=2.5,
        ))
        correction.add(Step(
            title=f"Probabilité cumulée P(X ≤ {k})",
            result_latex=f"P(X \\leq {k}) = \\sum_{{i=0}}^{{{k}}} P(X=i) = {latex(analysis.cumulative_le)} \\approx {float(analysis.cumulative_le):.4f}",
            explanation="On additionne les probabilités de tous les résultats inférieurs ou égaux à k.",
            weight=1.5,
        ))
        correction.add(Step(
            title=f"Probabilité cumulée P(X ≥ {k})",
            result_latex=f"P(X \\geq {k}) = \\sum_{{i={k}}}^{{{n}}} P(X=i) = {latex(analysis.cumulative_ge)} \\approx {float(analysis.cumulative_ge):.4f}",
            explanation="On additionne les probabilités de tous les résultats supérieurs ou égaux à k.",
            weight=1.5,
        ))

    correction.add(Step(
        title="Espérance, variance, écart-type",
        result_latex=(
            f"E(X) = np = {latex(analysis.expectation)} \\qquad "
            f"V(X) = np(1-p) = {latex(analysis.variance)} \\qquad "
            f"\\sigma(X) = \\sqrt{{V(X)}} = {latex(analysis.std_dev)}"
        ),
        explanation=(
            "Pour une loi binomiale, l'espérance, la variance et l'écart-type se "
            "calculent directement à partir de n et p, sans avoir besoin de sommer "
            "sur toutes les valeurs de X."
        ),
        rule_recalled="E(X) = np \\qquad V(X) = np(1-p) \\qquad \\sigma(X) = \\sqrt{np(1-p)}",
        weight=2.0,
    ))

    total = sum(pr for _, pr in analysis.distribution_table)
    correction.add(Step(
        title="Vérification : la loi est bien une loi de probabilité",
        result_latex=f"\\sum_{{i=0}}^{{{n}}} P(X=i) = {latex(sp.simplify(total))}",
        explanation="On vérifie que la somme des probabilités de toutes les valeurs possibles de X vaut bien 1 — un garde-fou simple contre une erreur de calcul.",
        weight=1.0,
    ))

    correction.compute_score()
    return correction
