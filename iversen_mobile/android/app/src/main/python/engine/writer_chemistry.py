"""
Rédacteur pédagogique pour l'équilibrage d'équations chimiques.
"""
from .chemistry import ChemistryAnalysis, parse_formula, formula_to_latex
from .models import Correction, Step


def write_chemistry_correction(exercise_title, equation_str, analysis: ChemistryAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=equation_str,
                             subject_line=f"{' + '.join(analysis.reactants)} → {' + '.join(analysis.products)}")

    correction.add(Step(
        title="Éléments chimiques en présence",
        result_latex=f"\\text{{Éléments : }} {', '.join(analysis.elements)}",
        explanation="On identifie tous les éléments chimiques présents dans les réactifs et les produits : chacun doit être présent en quantité égale de part et d'autre de la réaction.",
        weight=1.0,
    ))

    correction.add(Step(
        title="Mise en équation (conservation des éléments)",
        result_latex="\\text{Pour chaque élément : (quantité dans les réactifs) = (quantité dans les produits)}",
        explanation=(
            "On note a, b, c... les coefficients stœchiométriques inconnus de chaque "
            "composé, et on écrit une équation de conservation pour chaque élément "
            "chimique : cela donne un système linéaire à résoudre."
        ),
        rule_recalled="\\text{Loi de Lavoisier : rien ne se perd, rien ne se crée — chaque atome se retrouve à l'identique des deux côtés.}",
        weight=1.5,
    ))

    correction.add(Step(
        title="Résolution du système linéaire",
        result_latex="\\text{Système résolu par recherche du noyau de la matrice de composition}",
        explanation="Le système linéaire (un système homogène) admet une famille de solutions ; on choisit la solution en nombres entiers positifs la plus simple (sans diviseur commun).",
        weight=1.5,
    ))

    # Chaque nom de compose est converti en LaTeX avec indices numeriques
    # (H_{2}O) plutot que du texte brut (H2O), pour un affichage correct.
    coeffs_str = ", \\ ".join(
        f"{formula_to_latex(name)} : {c}"
        for name, c in zip(analysis.reactants + analysis.products, analysis.coefficients)
    )
    correction.add(Step(
        title="Coefficients stœchiométriques trouvés",
        result_latex=coeffs_str,
        explanation="Ce sont les plus petits coefficients entiers positifs qui équilibrent l'équation.",
        weight=1.5,
    ))

    def _fmt_side_latex(names, coeffs):
        parts = []
        for name, c in zip(names, coeffs):
            f = formula_to_latex(name)
            parts.append(f if c == 1 else f"{c}\\,{f}")
        return " + ".join(parts)

    n_reactants = len(analysis.reactants)
    balanced_latex = (
        f"{_fmt_side_latex(analysis.reactants, analysis.coefficients[:n_reactants])} "
        f"\\rightarrow "
        f"{_fmt_side_latex(analysis.products, analysis.coefficients[n_reactants:])}"
    )
    correction.add(Step(
        title="Équation équilibrée",
        result_latex=balanced_latex,
        explanation="L'équation-bilan complète, avec tous les coefficients stœchiométriques.",
        weight=2.0,
    ))

    checks = []
    all_ok = True
    for el in analysis.elements:
        left_count = sum(
            analysis.coefficients[i] * parse_formula(name).get(el, 0)
            for i, name in enumerate(analysis.reactants)
        )
        right_count = sum(
            analysis.coefficients[n_reactants + i] * parse_formula(name).get(el, 0)
            for i, name in enumerate(analysis.products)
        )
        ok = left_count == right_count
        all_ok = all_ok and ok
        checks.append(f"{el}: {left_count} = {right_count}" if ok else f"{el}: {left_count} \\neq {right_count} \\ (ERREUR)")

    # Le separateur "\quad" contient un backslash : on le construit hors de la
    # f-string (Python 3.11, utilise pour armeabi-v7a, interdit tout
    # backslash dans la partie {} d'une f-string, contrairement a 3.12+).
    checks_str = " \\quad ".join(checks)
    correction.add(Step(
        title="Vérification élément par élément",
        result_latex=checks_str,
        explanation="On recompte chaque élément de part et d'autre avec les coefficients trouvés : chaque total doit coïncider exactement.",
        weight=1.5,
        is_complete=all_ok,
        warning=None if all_ok else "Incohérence détectée dans la conservation d'un élément — l'équilibrage ne devrait normalement jamais produire ce cas.",
    ))

    correction.compute_score()
    return correction
