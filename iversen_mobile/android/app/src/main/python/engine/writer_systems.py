"""
Rédacteur pédagogique pour les systèmes de 2 équations linéaires — méthode de
substitution reconstituée pas à pas, cohérente avec le résultat déjà validé par
sp.linsolve() dans engine/systems.py.
"""
import sympy as sp
from sympy import latex
from .systems import SystemAnalysis, x, y
from .models import Correction, Step


def write_system_correction(exercise_title: str, equation1_str: str, equation2_str: str,
                             analysis: SystemAnalysis) -> Correction:
    system_label = f"{equation1_str}  ;  {equation2_str}"
    correction = Correction(exercise_title=exercise_title, function_str=system_label,
                             subject_line=f"Système : {{ {equation1_str} ; {equation2_str} }}")

    correction.add(Step(
        title="Mise en évidence du système",
        result_latex=f"\\begin{{cases}} {latex(analysis.eq1.lhs)} = {latex(analysis.eq1.rhs)} \\\\ {latex(analysis.eq2.lhs)} = {latex(analysis.eq2.rhs)} \\end{{cases}}",
        explanation="On dispose de deux équations à deux inconnues (x et y) : il faut les combiner pour trouver les valeurs qui vérifient les deux simultanément.",
        weight=1.0,
    ))

    if analysis.kind == "unique":
        sv, ov = analysis.substitution_variable, analysis.other_variable
        correction.add(Step(
            title=f"Isolement de {sv} dans la première équation",
            result_latex=f"{sv} = {latex(analysis.substitution_expr)}",
            explanation=f"On exprime {sv} en fonction de {ov} à partir de la première équation, pour pouvoir le remplacer dans la seconde (méthode de substitution).",
            rule_recalled="\\text{Méthode de substitution : isoler une inconnue dans une équation, la remplacer dans l'autre.}",
            weight=2.0,
        ))
        substituted_eq2 = sp.simplify(analysis.eq2.lhs.subs(sv, analysis.substitution_expr) - analysis.eq2.rhs.subs(sv, analysis.substitution_expr))
        correction.add(Step(
            title="Substitution dans la seconde équation",
            result_latex=f"{latex(substituted_eq2)} = 0 \\quad \\Rightarrow \\quad {ov} = {latex(analysis.other_value)}",
            explanation=f"En remplaçant {sv} par son expression dans la deuxième équation, on obtient une équation à une seule inconnue ({ov}), qu'on résout directement.",
            weight=2.0,
        ))
        correction.add(Step(
            title=f"Retour pour trouver {sv}",
            result_latex=f"{sv} = {latex(analysis.substitution_expr)} = {latex(analysis.substitution_value)}",
            explanation=f"On substitue la valeur de {ov} trouvée dans l'expression de {sv} obtenue à la première étape.",
            weight=1.5,
        ))
        x_val = analysis.other_value if ov == x else analysis.substitution_value
        y_val = analysis.other_value if ov == y else analysis.substitution_value
        correction.add(Step(
            title="Solution du système",
            result_latex=f"\\mathcal{{S}} = \\left\\{{ ({latex(x_val)} \\, ; \\, {latex(y_val)}) \\right\\}}",
            explanation="Le système admet un unique couple solution (x ; y).",
            weight=1.5,
        ))
        check1 = sp.simplify(analysis.eq1.lhs.subs({x: x_val, y: y_val}) - analysis.eq1.rhs.subs({x: x_val, y: y_val}))
        check2 = sp.simplify(analysis.eq2.lhs.subs({x: x_val, y: y_val}) - analysis.eq2.rhs.subs({x: x_val, y: y_val}))
        correction.add(Step(
            title="Vérification",
            result_latex=f"\\text{{éq. 1 : }} {latex(check1)} = 0 \\qquad \\text{{éq. 2 : }} {latex(check2)} = 0",
            explanation="On substitue la solution trouvée dans les deux équations de départ : les deux doivent bien redonner 0.",
            weight=1.0,
        ))

    elif analysis.kind == "aucune":
        correction.add(Step(
            title="Système incompatible",
            result_latex="\\mathcal{S} = \\varnothing",
            explanation=(
                "En combinant les deux équations, on aboutit à une égalité fausse "
                "(par exemple 0 = k avec k ≠ 0) : les deux droites représentées par "
                "ces équations sont strictement parallèles (même coefficient directeur, "
                "ordonnées à l'origine différentes) et ne se croisent jamais."
            ),
            weight=2.5,
        ))

    else:  # infinité
        correction.add(Step(
            title="Système indéterminé",
            result_latex=f"\\mathcal{{S}} = \\left\\{{ ({analysis.general_solution}) \\right\\}}",
            explanation=(
                "Les deux équations sont en réalité équivalentes (l'une est un multiple "
                "de l'autre) : elles décrivent la même droite. Tout couple (x, y) vérifiant "
                "l'une des deux équations vérifie automatiquement l'autre — il y a une "
                "infinité de solutions, décrites par un paramètre libre."
            ),
            weight=2.5,
        ))

    correction.compute_score()
    return correction
