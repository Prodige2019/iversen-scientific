"""
Rédacteur pédagogique pour la géométrie analytique dans le plan.
"""
from sympy import latex
from .geometry import GeometryAnalysis
from .models import Correction, Step


def write_geometry_correction(exercise_title, points_label, analysis: GeometryAnalysis) -> Correction:
    A, B = analysis.A, analysis.B
    subject = f"A({latex(A[0])} ; {latex(A[1])}), B({latex(B[0])} ; {latex(B[1])})"
    if analysis.C:
        subject += f", C({latex(analysis.C[0])} ; {latex(analysis.C[1])})"

    correction = Correction(exercise_title=exercise_title, function_str=points_label, subject_line=subject)

    correction.add(Step(
        title="Coordonnées du vecteur AB",
        result_latex=f"\\overrightarrow{{AB}} \\begin{{pmatrix}} x_B - x_A \\\\ y_B - y_A \\end{{pmatrix}} = \\begin{{pmatrix}} {latex(analysis.vector_AB[0])} \\\\ {latex(analysis.vector_AB[1])} \\end{{pmatrix}}",
        explanation="Les coordonnées d'un vecteur AB s'obtiennent en soustrayant les coordonnées de A à celles de B.",
        rule_recalled="\\overrightarrow{AB}\\begin{pmatrix} x_B-x_A \\\\ y_B-y_A \\end{pmatrix}",
        weight=1.5,
    ))

    correction.add(Step(
        title="Distance AB",
        result_latex=f"AB = \\sqrt{{(x_B-x_A)^2+(y_B-y_A)^2}} = {latex(analysis.distance_AB)}",
        explanation="La distance AB est la norme du vecteur AB, calculée grâce au théorème de Pythagore appliqué dans le repère.",
        rule_recalled="AB = \\sqrt{(x_B-x_A)^2 + (y_B-y_A)^2}",
        weight=1.5,
    ))

    correction.add(Step(
        title="Milieu du segment [AB]",
        result_latex=f"I = \\left( \\dfrac{{x_A+x_B}}{{2}} \\, ; \\, \\dfrac{{y_A+y_B}}{{2}} \\right) = ({latex(analysis.midpoint_AB[0])} \\, ; \\, {latex(analysis.midpoint_AB[1])})",
        explanation="Les coordonnées du milieu sont la moyenne des coordonnées des deux extrémités.",
        weight=1.0,
    ))

    if analysis.line_is_vertical:
        correction.add(Step(
            title="Équation de la droite (AB)",
            result_latex=f"x = {latex(analysis.line_x_value)}",
            explanation="Comme A et B ont la même abscisse, la droite (AB) est verticale : son équation est de la forme x = constante.",
            weight=1.5,
        ))
    else:
        correction.add(Step(
            title="Équation de la droite (AB)",
            result_latex=f"y = {latex(analysis.line_slope)}\\,x + {latex(analysis.line_intercept)}",
            explanation="Le coefficient directeur se calcule à partir des coordonnées de A et B, puis l'ordonnée à l'origine en substituant les coordonnées de A (ou B) dans y = mx + p.",
            rule_recalled="m = \\dfrac{y_B-y_A}{x_B-x_A} \\qquad p = y_A - m\\,x_A",
            weight=1.5,
        ))

    if analysis.C is not None:
        correction.add(Step(
            title="Coordonnées du vecteur AC",
            result_latex=f"\\overrightarrow{{AC}} \\begin{{pmatrix}} {latex(analysis.vector_AC[0])} \\\\ {latex(analysis.vector_AC[1])} \\end{{pmatrix}}",
            explanation="Même méthode que pour AB, appliquée à C.",
            weight=1.0,
        ))
        collinear_text = "A, B, C \\text{ sont alignés}" if analysis.are_collinear else "A, B, C \\text{ ne sont pas alignés}"
        correction.add(Step(
            title="Alignement de A, B, C",
            result_latex=f"\\det(\\overrightarrow{{AB}}, \\overrightarrow{{AC}}) = x_{{AB}}\\,y_{{AC}} - y_{{AB}}\\,x_{{AC}} = {latex(analysis.cross_product)} \\quad\\Rightarrow\\quad {collinear_text}",
            explanation="Deux vecteurs sont colinéaires (et donc les trois points alignés) si et seulement si leur déterminant est nul.",
            rule_recalled="\\overrightarrow{u}, \\overrightarrow{v} \\text{ colinéaires} \\iff \\det(\\overrightarrow{u},\\overrightarrow{v}) = 0",
            weight=2.0,
        ))
        ortho_text = "\\overrightarrow{AB} \\perp \\overrightarrow{AC}" if analysis.are_orthogonal else "\\text{pas orthogonaux}"
        correction.add(Step(
            title="Orthogonalité de AB et AC",
            result_latex=f"\\overrightarrow{{AB}} \\cdot \\overrightarrow{{AC}} = x_{{AB}}x_{{AC}} + y_{{AB}}y_{{AC}} = {latex(analysis.dot_product)} \\quad\\Rightarrow\\quad {ortho_text}",
            explanation="Deux vecteurs sont orthogonaux si et seulement si leur produit scalaire est nul.",
            rule_recalled="\\overrightarrow{u} \\perp \\overrightarrow{v} \\iff \\overrightarrow{u}\\cdot\\overrightarrow{v} = 0",
            weight=2.0,
        ))

    correction.compute_score()
    return correction
