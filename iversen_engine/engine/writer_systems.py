"""
Rédacteur pédagogique pour les systèmes d'équations linéaires (2, 3, 4
équations, autant d'inconnues parmi x, y, z, t) — généralisé, remplace la
version limitée à 2 équations en x, y.
"""
import sympy as sp
from sympy import latex
from .systems import SystemAnalysis
from .models import Correction, Step


def write_system_correction(exercise_title: str, equation_strs, analysis: SystemAnalysis) -> Correction:
    system_label = "  ;  ".join(equation_strs)
    var_names = ", ".join(str(v) for v in analysis.variables)
    correction = Correction(
        exercise_title=exercise_title, function_str=system_label,
        subject_line=f"Système ({len(equation_strs)} équations, inconnues : {var_names}) : {{ {system_label} }}",
    )

    cases_body = " \\\\ ".join(f"{latex(eq.lhs)} = {latex(eq.rhs)}" for eq in analysis.equations)
    correction.add(Step(
        title="Mise en évidence du système",
        result_latex=f"\\begin{{cases}} {cases_body} \\end{{cases}}",
        explanation=(
            f"On dispose de {len(analysis.equations)} équations à {len(analysis.variables)} "
            f"inconnue(s) ({var_names}) : il faut trouver les valeurs qui vérifient "
            f"toutes les équations simultanément."
        ),
        weight=1.0,
    ))

    if analysis.kind == "unique":
        correction.add(Step(
            title="Résolution du système",
            result_latex=(
                "\\text{Résolution par élimination/substitution successive "
                "(méthode générale), le résultat étant obtenu par calcul "
                "matriciel exact (SymPy).}"
            ),
            explanation=(
                "Pour un système à plusieurs équations et plusieurs inconnues, "
                "la méthode générale consiste à éliminer les inconnues une par "
                "une (par combinaison ou substitution) jusqu'à n'en garder "
                "qu'une seule à résoudre, puis remonter par substitutions "
                "successives pour retrouver toutes les autres."
            ),
            rule_recalled=(
                "\\text{Un système linéaire admet 0, 1, ou une infinité de "
                "solutions — jamais un nombre fini strictement supérieur à 1.}"
            ),
            weight=2.5,
        ))

        solution_parts = ", \\ ".join(
            f"{latex(var)} = {latex(val)}" for var, val in analysis.solution.items()
        )
        correction.add(Step(
            title="Solution du système",
            result_latex=f"\\mathcal{{S}} = \\left\\{{ ({solution_parts}) \\right\\}}",
            explanation=f"Le système admet un unique {len(analysis.variables)}-uplet solution.",
            weight=1.5,
        ))

        checks = []
        all_ok = True
        for i, eq in enumerate(analysis.equations, start=1):
            check = sp.simplify(eq.lhs.subs(analysis.solution) - eq.rhs.subs(analysis.solution))
            ok = check == 0
            all_ok = all_ok and ok
            checks.append(f"\\text{{éq. {i} : }} {latex(check)} = 0" if ok else f"\\text{{éq. {i} : ÉCART }} {latex(check)}")
        correction.add(Step(
            title="Vérification",
            result_latex=" \\qquad ".join(checks),
            explanation="On substitue la solution trouvée dans toutes les équations de départ : chacune doit bien redonner une égalité vraie.",
            weight=1.0,
            is_complete=all_ok,
            warning=None if all_ok else "Incohérence détectée — ne devrait normalement jamais se produire.",
        ))

    elif analysis.kind == "aucune":
        correction.add(Step(
            title="Système incompatible",
            result_latex="\\mathcal{S} = \\varnothing",
            explanation=(
                "En combinant les équations, on aboutit à une égalité fausse "
                "(par exemple 0 = k avec k ≠ 0) : les conditions imposées par "
                "le système sont contradictoires, il n'existe aucune solution "
                "commune."
            ),
            weight=2.5,
        ))

    else:  # infinité
        correction.add(Step(
            title="Système indéterminé",
            result_latex=f"\\mathcal{{S}} : \\ {analysis.general_solution}",
            explanation=(
                "Le nombre d'équations réellement indépendantes est inférieur "
                "au nombre d'inconnues : au moins une inconnue reste libre "
                "(elle peut prendre n'importe quelle valeur réelle), les autres "
                "s'exprimant en fonction d'elle. Il y a donc une infinité de "
                "solutions."
            ),
            weight=2.5,
        ))

    correction.compute_score()
    return correction
