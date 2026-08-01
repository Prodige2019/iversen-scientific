"""
Rédacteur pédagogique pour la stœchiométrie (quantités de matière et masses).
"""
import sympy as sp
from sympy import latex
from .chemistry import formula_to_latex
from .chemistry_stoichiometry import StoichiometryAnalysis
from .models import Correction, Step


def _balanced_equation_latex(eq) -> str:
    n_reactants = len(eq.reactants)

    def side(names, coeffs):
        parts = []
        for name, c in zip(names, coeffs):
            f = formula_to_latex(name)
            parts.append(f if c == 1 else f"{c}\\,{f}")
        return " + ".join(parts)

    return (
        f"{side(eq.reactants, eq.coefficients[:n_reactants])} "
        f"\\rightarrow "
        f"{side(eq.products, eq.coefficients[n_reactants:])}"
    )


def write_stoichiometry_correction(exercise_title, equation_str, known_compound,
                                    amount_str, amount_type, analysis: StoichiometryAnalysis) -> Correction:
    kc = formula_to_latex(known_compound)
    balanced_latex = _balanced_equation_latex(analysis.equation)

    correction = Correction(
        exercise_title=exercise_title, function_str=equation_str,
        subject_line=f"{analysis.equation.balanced_equation.replace('->', '→')}, "
                     f"{amount_str}\\,{'mol' if amount_type=='mol' else 'g'} de {known_compound}",
    )

    correction.add(Step(
        title="Équation équilibrée",
        result_latex=balanced_latex,
        explanation="On part de l'équation-bilan équilibrée : les coefficients stœchiométriques donnent les proportions molaires entre les composés.",
        weight=1.0,
    ))

    known = next(q for q in analysis.quantities if q.name == known_compound)
    if amount_type == "g":
        correction.add(Step(
            title=f"Masse molaire de {known_compound}",
            result_latex=f"M({kc}) = {latex(sp.nsimplify(known.molar_mass, rational=False))}\\,g/mol",
            explanation="On calcule la masse molaire en sommant les masses atomiques de chaque élément de la formule, pondérées par leur nombre d'occurrences.",
            weight=1.5,
        ))
        correction.add(Step(
            title=f"Quantité de matière connue ({known_compound})",
            result_latex=f"n({kc}) = \\dfrac{{m}}{{M}} = \\dfrac{{{amount_str}}}{{{latex(sp.nsimplify(known.molar_mass, rational=False))}}} = {latex(sp.N(known.moles, 4))}\\,mol",
            explanation="La quantité de matière se déduit de la masse et de la masse molaire.",
            rule_recalled="n = \\dfrac{m}{M}",
            weight=1.5,
        ))
    else:
        correction.add(Step(
            title=f"Quantité de matière connue ({known_compound})",
            result_latex=f"n({kc}) = {latex(known.moles)}\\,mol \\quad \\text{{(donnée directement)}}",
            explanation="La quantité de matière du composé de référence est donnée directement dans l'énoncé.",
            weight=1.0,
        ))

    correction.add(Step(
        title="Proportionnalité stœchiométrique",
        result_latex=f"\\text{{Pour chaque composé X de coefficient }} c_X : \\quad n(X) = n({kc}) \\times \\dfrac{{c_X}}{{{known.coefficient}}}",
        explanation="Les quantités de matière de tous les composés sont proportionnelles à leurs coefficients stœchiométriques respectifs dans l'équation équilibrée.",
        rule_recalled="\\dfrac{n(A)}{c_A} = \\dfrac{n(B)}{c_B} = \\ldots",
        weight=2.0,
    ))

    lines = []
    for q in analysis.quantities:
        qname = formula_to_latex(q.name)
        lines.append(
            f"{qname} \\ (c={q.coefficient}) : \\ n = {latex(sp.N(q.moles, 4))}\\,mol, \\ "
            f"M = {latex(sp.N(q.molar_mass, 4))}\\,g/mol, \\ m = {latex(sp.N(q.mass, 4))}\\,g"
        )
    correction.add(Step(
        title="Quantités de matière et masses de tous les composés",
        result_latex=" \\\\ ".join(lines),
        explanation="On applique la proportionnalité à chaque composé pour obtenir sa quantité de matière, puis sa masse (m = n × M).",
        rule_recalled="m = n \\times M",
        weight=2.5,
    ))

    total_reactant_mass = sp.simplify(sum(
        q.mass for q in analysis.quantities if q.name in analysis.equation.reactants
    ))
    total_product_mass = sp.simplify(sum(
        q.mass for q in analysis.quantities if q.name in analysis.equation.products
    ))
    mass_gap = sp.N(total_reactant_mass - total_product_mass, 6)
    correction.add(Step(
        title="Vérification : conservation de la masse totale",
        result_latex=(
            f"m_{{réactifs}} = {latex(sp.N(total_reactant_mass, 4))}\\,g \\qquad "
            f"m_{{produits}} = {latex(sp.N(total_product_mass, 4))}\\,g \\qquad "
            f"\\text{{écart : }} {latex(mass_gap)}\\,g"
        ),
        explanation="La masse totale des réactifs consommés doit être égale à la masse totale des produits formés (loi de Lavoisier) : c'est un garde-fou de cohérence contre une erreur de calcul.",
        weight=1.5,
        is_complete=abs(float(mass_gap)) < 1e-6,
        warning=None if abs(float(mass_gap)) < 1e-6 else "Écart de masse détecté — ne devrait normalement jamais se produire.",
    ))

    correction.compute_score()
    return correction
