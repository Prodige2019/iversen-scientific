"""
Moteur de calcul matriciel — analyse d'une matrice (déterminant, trace, transposée,
inverse, rang) et opérations entre deux matrices (somme, produit). Calcul exact via
SymPy (fractions, pas de flottants), même philosophie que le reste du projet.
"""
from dataclasses import dataclass
from typing import List, Optional
import sympy as sp
from .equations import parse_math_expression


@dataclass
class MatrixAnalysis:
    M: sp.Matrix
    determinant: Optional[sp.Expr] = None   # None si la matrice n'est pas carrée
    trace: Optional[sp.Expr] = None
    transpose: sp.Matrix = None
    rank: int = 0
    is_invertible: Optional[bool] = None
    inverse: Optional[sp.Matrix] = None


@dataclass
class MatrixOperationResult:
    A: sp.Matrix
    B: sp.Matrix
    operation: str          # "somme" | "produit"
    result: sp.Matrix


def parse_matrix(rows: List[List[str]]) -> sp.Matrix:
    """Construit une sp.Matrix à partir d'une liste de lignes de chaînes de
    caractères (ex: [["1","2"],["3","4"]]), avec validation de rectangularité."""
    if not rows or not all(rows):
        raise ValueError("La matrice ne peut pas être vide.")
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        raise ValueError("Toutes les lignes de la matrice doivent avoir le même nombre de colonnes.")
    try:
        parsed = [[sp.nsimplify(parse_math_expression(cell)) for cell in row] for row in rows]
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Coefficient illisible dans la matrice. Détail : {e}")
    return sp.Matrix(parsed)


def analyze_matrix(rows: List[List[str]]) -> MatrixAnalysis:
    M = parse_matrix(rows)
    is_square = M.rows == M.cols

    determinant = None
    trace = None
    is_invertible = None
    inverse = None

    if is_square:
        determinant = sp.simplify(M.det())
        trace = sp.simplify(M.trace())
        is_invertible = determinant != 0
        if is_invertible:
            inverse = sp.simplify(M.inv())

    return MatrixAnalysis(
        M=M, determinant=determinant, trace=trace, transpose=M.T,
        rank=M.rank(), is_invertible=is_invertible, inverse=inverse,
    )


def compute_matrix_operation(rows_a: List[List[str]], rows_b: List[List[str]], operation: str) -> MatrixOperationResult:
    A = parse_matrix(rows_a)
    B = parse_matrix(rows_b)

    if operation == "somme":
        if A.shape != B.shape:
            raise ValueError(
                f"La somme de deux matrices exige des dimensions identiques "
                f"(reçu {A.shape} et {B.shape})."
            )
        result = A + B
    elif operation == "produit":
        if A.cols != B.rows:
            raise ValueError(
                f"Le produit A×B exige que le nombre de colonnes de A ({A.cols}) "
                f"soit égal au nombre de lignes de B ({B.rows})."
            )
        result = A * B
    else:
        raise ValueError(f"Opération inconnue : « {operation} » (attendu : « somme » ou « produit »).")

    return MatrixOperationResult(A=A, B=B, operation=operation, result=sp.simplify(result))
