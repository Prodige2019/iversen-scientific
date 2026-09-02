"""
Rédacteur pédagogique pour la résolution d'équations — même logique que
engine/writer.py : templates conditionnels, pas de génération libre.
"""
import sympy as sp
from sympy import latex
from .equations import EquationAnalysis, x
from .models import Correction, Step
from .set_notation import french_set_latex as _set_to_latex


def write_equation_correction(exercise_title: str, equation_str: str, analysis: EquationAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=equation_str,
                             subject_line=f"Équation : {equation_str}")

    # Étape 1 — mise en forme normalisée
    correction.add(Step(
        title="Mise en équation normalisée",
        result_latex=f"{latex(analysis.normalized)} = 0",
        explanation=(
            "On ramène l'équation à la forme « expression = 0 » en soustrayant le membre "
            "de droite au membre de gauche : cela permet d'identifier directement le type "
            "d'équation (linéaire, quadratique, ...)."
        ),
        weight=1.0,
    ))

    if analysis.kind == "linéaire":
        a, b = analysis.coefficients
        correction.add(Step(
            title="Équation linéaire : isolement de x",
            result_latex=f"{latex(a)}x + {latex(b)} = 0 \\quad \\Rightarrow \\quad x = -\\frac{{{latex(b)}}}{{{latex(a)}}}",
            explanation="Une équation du premier degré ax + b = 0 (avec a ≠ 0) a une unique solution : x = -b/a.",
            rule_recalled="ax + b = 0 \\iff x = -\\dfrac{b}{a} \\quad (a \\neq 0)",
            weight=2.0,
        ))
        sol = analysis.solutions[0] if analysis.solutions else None
        correction.add(Step(
            title="Solution",
            result_latex=f"\\mathcal{{S}} = \\left\\{{ {latex(sol)} \\right\\}}" if sol is not None else "\\text{aucune solution}",
            explanation="L'ensemble des solutions ne contient que cette unique valeur.",
            weight=1.5,
        ))

    elif analysis.kind == "quadratique":
        a, b, c = analysis.coefficients
        d = analysis.discriminant
        correction.add(Step(
            title="Identification des coefficients",
            result_latex=f"a = {latex(a)}, \\quad b = {latex(b)}, \\quad c = {latex(c)}",
            explanation="On identifie les coefficients de la forme générale ax² + bx + c = 0.",
            weight=1.0,
        ))
        correction.add(Step(
            title="Calcul du discriminant",
            result_latex=f"\\Delta = b^2 - 4ac = {latex(d)}",
            explanation="Le discriminant Δ détermine le nombre de solutions réelles de l'équation.",
            rule_recalled="\\Delta = b^2 - 4ac",
            weight=2.0,
        ))

        if d is not None and d.is_real and d > 0:
            r1, r2 = analysis.solutions
            correction.add(Step(
                title="Δ > 0 : deux solutions réelles distinctes",
                result_latex=(
                    f"x_1 = \\dfrac{{-b - \\sqrt{{\\Delta}}}}{{2a}} = {latex(r1)} "
                    f"\\qquad x_2 = \\dfrac{{-b + \\sqrt{{\\Delta}}}}{{2a}} = {latex(r2)}"
                ),
                explanation="Δ étant strictement positif, l'équation admet deux racines réelles distinctes.",
                rule_recalled="x_{1,2} = \\dfrac{-b \\pm \\sqrt{\\Delta}}{2a}",
                weight=2.0,
            ))
            sol_latex = f"\\left\\{{ {latex(r1)} ; {latex(r2)} \\right\\}}"
        elif d is not None and d.is_real and d == 0:
            r0 = analysis.solutions[0]
            correction.add(Step(
                title="Δ = 0 : une solution double",
                result_latex=f"x_0 = \\dfrac{{-b}}{{2a}} = {latex(r0)}",
                explanation="Δ étant nul, l'équation admet une unique racine, dite double (de multiplicité 2).",
                rule_recalled="x_0 = -\\dfrac{b}{2a}",
                weight=2.0,
            ))
            sol_latex = f"\\left\\{{ {latex(r0)} \\right\\}}"
        elif d is not None and d.is_real and d < 0:
            correction.add(Step(
                title="Δ < 0 : aucune solution réelle",
                result_latex="\\mathcal{S} = \\varnothing \\text{ dans } \\mathbb{R}",
                explanation=(
                    "Δ étant strictement négatif, l'équation n'a pas de racine réelle "
                    "(elle a deux racines complexes conjuguées, hors programme à ce niveau)."
                ),
                weight=2.0,
            ))
            sol_latex = "\\varnothing"
        else:
            sol_latex = "\\text{non déterminé automatiquement}"

        correction.add(Step(
            title="Ensemble des solutions",
            result_latex=f"\\mathcal{{S}} = {sol_latex}",
            explanation="On récapitule l'ensemble des solutions trouvées.",
            weight=1.5,
        ))

    elif analysis.kind == "avec racine":
        correction.add(Step(
            title="Domaine de validité",
            result_latex=f"\\mathcal{{D}} = {_set_to_latex(analysis.domain)}",
            explanation=(
                "Une racine carrée (ou n-ième d'indice pair) n'est définie, dans ℝ, que si "
                "la quantité qu'elle contient est positive ou nulle. On détermine donc d'abord "
                "l'ensemble des valeurs de x pour lesquelles chaque membre de l'équation a un sens : "
                "toute solution devra obligatoirement appartenir à cet ensemble."
            ),
            rule_recalled="\\sqrt{u(x)} \\text{ est définie ssi } u(x) \\geq 0",
            weight=1.5,
        ))
        raw_candidates = analysis.solutions + [c for c, _ in analysis.rejected_solutions]
        candidates_latex = " \\, ; \\, ".join(latex(s) for s in raw_candidates) if raw_candidates else "\\text{aucun}"
        correction.add(Step(
            title="Élévation à la puissance adaptée",
            result_latex=f"\\text{{candidat(s) : }} {candidates_latex}",
            explanation=(
                "On isole le radical puis on élève les deux membres à la puissance qui l'élimine "
                "(au carré pour une racine carrée, au cube pour une racine cubique, etc.). Cette "
                "opération n'est pas toujours réversible : elle peut introduire des solutions "
                "« étrangères » qui ne vérifient pas l'équation de départ — d'où la vérification "
                "systématique qui suit."
            ),
            weight=2.0,
        ))
        if analysis.rejected_solutions:
            rejected_latex = " \\quad ".join(
                f"x = {latex(s)} \\ (\\text{{{reason}}})" for s, reason in analysis.rejected_solutions
            )
            correction.add(Step(
                title="Vérification : élimination des solutions étrangères",
                result_latex=rejected_latex,
                explanation=(
                    "Chaque candidat doit être réinjecté dans l'équation ORIGINALE (pas dans la "
                    "version élevée au carré) et vérifier le domaine trouvé plus haut. Les candidats "
                    "listés ci-contre échouent à ce test et doivent donc être rejetés."
                ),
                weight=1.5,
            ))
        else:
            correction.add(Step(
                title="Vérification",
                result_latex="\\text{tous les candidats vérifient l'équation d'origine}",
                explanation="Chaque candidat a été réinjecté dans l'équation de départ : aucune solution étrangère à écarter ici.",
                weight=1.0,
            ))
        sol_latex = (f"\\left\\{{ {' ; '.join(latex(s) for s in analysis.solutions)} \\right\\}}"
                     if analysis.solutions else "\\varnothing")
        correction.add(Step(
            title="Ensemble des solutions",
            result_latex=f"\\mathcal{{S}} = {sol_latex}",
            explanation="On récapitule les seules solutions ayant passé la double vérification (domaine + équation d'origine).",
            weight=1.5,
            is_complete=analysis.solutions_are_complete,
            warning=None if analysis.solutions_are_complete else
                    "SymPy n'a pas garanti l'exhaustivité des solutions pour cette équation : à vérifier manuellement.",
        ))

    else:
        correction.add(Step(
            title="Résolution générale",
            result_latex="\\text{résolution symbolique (SymPy)}",
            explanation=(
                "L'équation n'est ni linéaire ni quadratique (degré supérieur, ou non "
                "polynomiale) : elle est résolue par les méthodes générales de calcul formel."
            ),
            weight=1.0,
        ))
        if analysis.solutions:
            sol_list = " \\, ; \\, ".join(latex(s) for s in analysis.solutions)
            correction.add(Step(
                title="Solutions trouvées",
                result_latex=f"\\mathcal{{S}} = \\left\\{{ {sol_list} \\right\\}}",
                explanation="Solutions réelles trouvées par résolution symbolique.",
                weight=2.0,
                is_complete=analysis.solutions_are_complete,
                warning=None if analysis.solutions_are_complete else
                        "SymPy n'a pas garanti l'exhaustivité des solutions pour cette équation : "
                        "à vérifier manuellement pour un cas hors programme standard.",
            ))
        else:
            correction.add(Step(
                title="Solutions trouvées",
                result_latex="\\text{aucune solution réelle trouvée automatiquement}",
                explanation="Aucune racine réelle n'a été identifiée par résolution symbolique.",
                weight=2.0,
                is_complete=analysis.solutions_are_complete,
            ))

    # Étape finale — vérification par substitution (sur au moins une solution, si elle existe)
    if analysis.solutions:
        s0 = analysis.solutions[0]
        check_value = sp.simplify(analysis.normalized.subs(x, s0))
        correction.add(Step(
            title="Vérification",
            result_latex=f"\\text{{en }} x = {latex(s0)} : \\quad {latex(analysis.normalized)} = {latex(check_value)}",
            explanation="On substitue une solution trouvée dans l'équation normalisée : on doit bien retrouver 0.",
            weight=1.0,
        ))

    correction.compute_score()
    return correction
