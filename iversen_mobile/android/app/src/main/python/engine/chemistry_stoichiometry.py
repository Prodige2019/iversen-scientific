"""
Moteur de stœchiométrie — calcule les quantités de matière (et masses) de tous
les composés d'une équation chimique équilibrée, à partir d'une quantité connue
d'un seul composé. Réutilise le parseur de formules et l'équilibrage déjà
construits dans engine/chemistry.py.
"""
from dataclasses import dataclass
from typing import Dict, List
import sympy as sp
from .equations import parse_math_expression

from .chemistry import balance_equation, parse_formula, ChemistryAnalysis

ATOMIC_MASSES: Dict[str, float] = {
    "H": 1.008, "He": 4.003, "Li": 6.94, "Be": 9.012, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.18, "Na": 22.99, "Mg": 24.305,
    "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.948,
    "K": 39.098, "Ca": 40.078, "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996,
    "Mn": 54.938, "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.63, "As": 74.922, "Se": 78.971, "Br": 79.904, "Kr": 83.798,
    "Rb": 85.468, "Sr": 87.62, "Ag": 107.868, "Cd": 112.414, "Sn": 118.71, "I": 126.904,
    "Ba": 137.327, "Au": 196.967, "Hg": 200.592, "Pb": 207.2,
}


def compute_molar_mass(formula: str) -> sp.Expr:
    composition = parse_formula(formula)
    unknown = [el for el in composition if el not in ATOMIC_MASSES]
    if unknown:
        raise ValueError(
            f"Élément(s) non reconnu(s) dans la table des masses molaires : {', '.join(unknown)}. "
            f"Formule : « {formula} »."
        )
    total = sum(sp.nsimplify(ATOMIC_MASSES[el]) * count for el, count in composition.items())
    return sp.simplify(total)


@dataclass
class CompoundQuantity:
    name: str
    coefficient: int
    molar_mass: sp.Expr
    moles: sp.Expr
    mass: sp.Expr


@dataclass
class StoichiometryAnalysis:
    equation: ChemistryAnalysis
    known_compound: str
    known_moles: sp.Expr
    quantities: List[CompoundQuantity]


def analyze_stoichiometry(equation_str: str, known_compound: str, amount_str: str, amount_type: str) -> StoichiometryAnalysis:
    equation = balance_equation(equation_str)
    all_compounds = equation.reactants + equation.products
    if known_compound not in all_compounds:
        raise ValueError(
            f"« {known_compound} » n'apparaît pas dans l'équation {equation.balanced_equation}. "
            f"Composés disponibles : {', '.join(all_compounds)}."
        )
    if amount_type not in ("mol", "g"):
        raise ValueError(f"Type de quantité inconnu : « {amount_type} » (attendu : « mol » ou « g »).")

    try:
        amount = sp.nsimplify(parse_math_expression(amount_str))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Quantité illisible : « {amount_str} ». Détail : {e}")
    if not (amount.is_real and amount > 0):
        raise ValueError(f"La quantité doit être strictement positive (reçu : {amount}).")

    known_molar_mass = compute_molar_mass(known_compound)
    known_moles = amount if amount_type == "mol" else sp.simplify(amount / known_molar_mass)

    idx_known = all_compounds.index(known_compound)
    coeff_known = equation.coefficients[idx_known]

    quantities = []
    for name, coeff in zip(all_compounds, equation.coefficients):
        molar_mass = compute_molar_mass(name)
        moles = sp.simplify(known_moles * sp.Rational(coeff, coeff_known))
        mass = sp.simplify(moles * molar_mass)
        quantities.append(CompoundQuantity(name=name, coefficient=coeff, molar_mass=molar_mass, moles=moles, mass=mass))

    return StoichiometryAnalysis(
        equation=equation, known_compound=known_compound, known_moles=known_moles, quantities=quantities,
    )
