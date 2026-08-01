"""
Moteur de géométrie analytique dans le plan — points, vecteurs, distances,
droites. Calcul exact via SymPy, même philosophie que le reste du projet.

Entrée : les coordonnées de deux points A, B (obligatoires) et, optionnellement,
un troisième point C (pour l'alignement, l'orthogonalité, l'angle).
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import sympy as sp
from .equations import parse_math_expression


Point = Tuple[sp.Expr, sp.Expr]


@dataclass
class GeometryAnalysis:
    A: Point
    B: Point
    C: Optional[Point]
    vector_AB: Point
    distance_AB: sp.Expr
    midpoint_AB: Point
    line_is_vertical: bool
    line_slope: Optional[sp.Expr]        # None si verticale
    line_intercept: Optional[sp.Expr]    # None si verticale
    line_x_value: Optional[sp.Expr]      # valeur de x si verticale
    vector_AC: Optional[Point] = None
    distance_AC: Optional[sp.Expr] = None
    cross_product: Optional[sp.Expr] = None
    dot_product: Optional[sp.Expr] = None
    are_collinear: Optional[bool] = None
    are_orthogonal: Optional[bool] = None


def _parse_point(coords, label: str) -> Point:
    if not isinstance(coords, (list, tuple)) or len(coords) != 2:
        raise ValueError(f"Le point {label} doit avoir exactement 2 coordonnées (x, y).")
    try:
        x = sp.nsimplify(parse_math_expression(coords[0]))
        y = sp.nsimplify(parse_math_expression(coords[1]))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Coordonnées du point {label} illisibles : {coords}. Détail : {e}")
    return (x, y)


def analyze_geometry(A_coords, B_coords, C_coords=None) -> GeometryAnalysis:
    A = _parse_point(A_coords, "A")
    B = _parse_point(B_coords, "B")
    if A == B:
        raise ValueError("Les points A et B doivent être distincts pour définir un vecteur et une droite.")

    vector_AB = (sp.simplify(B[0] - A[0]), sp.simplify(B[1] - A[1]))
    distance_AB = sp.simplify(sp.sqrt(vector_AB[0]**2 + vector_AB[1]**2))
    midpoint_AB = (sp.simplify((A[0] + B[0]) / 2), sp.simplify((A[1] + B[1]) / 2))

    line_is_vertical = vector_AB[0] == 0
    line_slope = line_intercept = line_x_value = None
    if line_is_vertical:
        line_x_value = A[0]
    else:
        line_slope = sp.simplify(vector_AB[1] / vector_AB[0])
        line_intercept = sp.simplify(A[1] - line_slope * A[0])

    result = GeometryAnalysis(
        A=A, B=B, C=None, vector_AB=vector_AB, distance_AB=distance_AB,
        midpoint_AB=midpoint_AB, line_is_vertical=line_is_vertical,
        line_slope=line_slope, line_intercept=line_intercept, line_x_value=line_x_value,
    )

    if C_coords is not None:
        C = _parse_point(C_coords, "C")
        if C == A:
            raise ValueError("Le point C doit être distinct du point A.")
        vector_AC = (sp.simplify(C[0] - A[0]), sp.simplify(C[1] - A[1]))
        distance_AC = sp.simplify(sp.sqrt(vector_AC[0]**2 + vector_AC[1]**2))
        cross = sp.simplify(vector_AB[0] * vector_AC[1] - vector_AB[1] * vector_AC[0])
        dot = sp.simplify(vector_AB[0] * vector_AC[0] + vector_AB[1] * vector_AC[1])

        result.C = C
        result.vector_AC = vector_AC
        result.distance_AC = distance_AC
        result.cross_product = cross
        result.dot_product = dot
        result.are_collinear = (cross == 0)
        result.are_orthogonal = (dot == 0)

    return result
