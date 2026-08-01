"""
Rédacteur pédagogique pour le calcul matriciel.
"""
import sympy as sp
from sympy import latex
from .matrices import MatrixAnalysis, MatrixOperationResult
from .models import Correction, Step


def write_matrix_correction(exercise_title, matrix_label, analysis: MatrixAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=matrix_label,
                             subject_line=f"M = {latex(analysis.M)}")

    correction.add(Step(
        title="Dimensions de la matrice",
        result_latex=f"M \\in \\mathcal{{M}}_{{{analysis.M.rows},{analysis.M.cols}}}(\\mathbb{{R}})",
        explanation=f"La matrice M a {analysis.M.rows} ligne(s) et {analysis.M.cols} colonne(s).",
        weight=0.5,
    ))

    correction.add(Step(
        title="Transposée",
        result_latex=f"M^T = {latex(analysis.transpose)}",
        explanation="La transposée s'obtient en échangeant les lignes et les colonnes de M.",
        rule_recalled="(M^T)_{i,j} = M_{j,i}",
        weight=1.0,
    ))

    if analysis.determinant is not None:
        correction.add(Step(
            title="Déterminant",
            result_latex=f"\\det(M) = {latex(analysis.determinant)}",
            explanation="Le déterminant est un scalaire caractéristique de la matrice, qui détermine notamment si elle est inversible.",
            weight=2.0,
        ))
        correction.add(Step(
            title="Trace",
            result_latex=f"\\text{{tr}}(M) = {latex(analysis.trace)}",
            explanation="La trace est la somme des coefficients diagonaux de M.",
            rule_recalled="\\text{tr}(M) = \\sum_i M_{i,i}",
            weight=1.0,
        ))

        if analysis.is_invertible:
            correction.add(Step(
                title="Inversibilité et inverse",
                result_latex=f"\\det(M) \\neq 0 \\quad\\Rightarrow\\quad M^{{-1}} = {latex(analysis.inverse)}",
                explanation="Le déterminant étant non nul, M est inversible ; on calcule son inverse.",
                rule_recalled="M \\text{ inversible} \\iff \\det(M) \\neq 0",
                weight=2.0,
            ))
            check = sp.simplify(analysis.M * analysis.inverse - sp.eye(analysis.M.rows))
            correction.add(Step(
                title="Vérification : M × M⁻¹ = I",
                result_latex=f"M \\times M^{{-1}} - I = {latex(check)}",
                explanation="On vérifie que le produit de M par son inverse calculé redonne bien la matrice identité.",
                weight=1.0,
            ))
        else:
            correction.add(Step(
                title="Inversibilité",
                result_latex="\\det(M) = 0 \\quad\\Rightarrow\\quad M \\text{ n'est pas inversible}",
                explanation="Le déterminant étant nul, M n'admet pas d'inverse.",
                weight=2.0,
            ))
    else:
        correction.add(Step(
            title="Déterminant",
            result_latex="\\text{non défini (matrice non carrée)}",
            explanation="Le déterminant et l'inverse ne sont définis que pour une matrice carrée.",
            weight=1.0,
        ))

    correction.add(Step(
        title="Rang",
        result_latex=f"\\text{{rg}}(M) = {analysis.rank}",
        explanation="Le rang est le nombre maximal de lignes (ou colonnes) linéairement indépendantes.",
        weight=1.0,
    ))

    correction.compute_score()
    return correction


def write_matrix_operation_correction(exercise_title, operation_label, result: MatrixOperationResult) -> Correction:
    op_symbol = "+" if result.operation == "somme" else "\\times"
    correction = Correction(exercise_title=exercise_title, function_str=operation_label,
                             subject_line=f"A {op_symbol} B, avec A = {latex(result.A)}, B = {latex(result.B)}")

    correction.add(Step(
        title="Vérification des dimensions",
        result_latex=f"A \\in \\mathcal{{M}}_{{{result.A.rows},{result.A.cols}}}, \\quad B \\in \\mathcal{{M}}_{{{result.B.rows},{result.B.cols}}}",
        explanation=(
            "Pour une somme, A et B doivent avoir les mêmes dimensions. "
            "Pour un produit A×B, le nombre de colonnes de A doit être égal au nombre de lignes de B."
        ),
        weight=1.0,
    ))

    if result.operation == "somme":
        correction.add(Step(
            title="Calcul terme à terme",
            result_latex=f"A + B = {latex(result.result)}",
            explanation="La somme de deux matrices s'obtient en additionnant les coefficients de même position.",
            rule_recalled="(A+B)_{i,j} = A_{i,j} + B_{i,j}",
            weight=2.5,
        ))
    else:
        correction.add(Step(
            title="Calcul du produit",
            result_latex=f"A \\times B = {latex(result.result)}",
            explanation="Chaque coefficient du produit est la somme des produits terme à terme d'une ligne de A par une colonne de B.",
            rule_recalled="(AB)_{i,j} = \\sum_k A_{i,k} \\, B_{k,j}",
            weight=2.5,
        ))

    correction.compute_score()
    return correction
