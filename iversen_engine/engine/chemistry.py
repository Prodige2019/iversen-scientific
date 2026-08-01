"""
Moteur d'équilibrage d'équations chimiques — parse les formules moléculaires
(avec parenthèses imbriquées, ex: Ca(OH)2, Al2(SO4)3) et résout l'équilibrage
comme un système linéaire (conservation de chaque élément), via le noyau
(nullspace) de la matrice de composition — approche standard et robuste,
pas une recherche par tâtonnement.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
import sympy as sp


@dataclass
class ChemistryAnalysis:
    reactants: List[str]
    products: List[str]
    coefficients: List[int]
    elements: List[str]
    composition_matrix: sp.Matrix
    balanced_equation: str


_TOKEN_RE = re.compile(r"([A-Z][a-z]?)(\d*)|(\()|(\))(\d*)")


def formula_to_latex(formula: str) -> str:
    """Convertit une formule chimique brute ('H2O', 'Ca(OH)2', 'Al2(SO4)3') en
    LaTeX avec les indices numériques correctement affichés en indice (H_{2}O),
    au lieu du texte brut où le chiffre apparaît à la même taille que les
    lettres."""
    def repl(m):
        element, count, open_paren, close_paren, close_count = m.groups()
        if element:
            return f"{element}_{{{count}}}" if count else element
        if open_paren:
            return "("
        if close_paren:
            return f")_{{{close_count}}}" if close_count else ")"
        return m.group(0)
    return _TOKEN_RE.sub(repl, formula)


def parse_formula(formula: str) -> Dict[str, int]:
    """Parse une formule moléculaire (avec parenthèses imbriquées) en comptage
    par élément, ex: 'Ca(OH)2' -> {'Ca': 1, 'O': 2, 'H': 2}."""
    formula = formula.strip()
    if not formula:
        raise ValueError("Formule chimique vide.")

    stack = [{}]
    pos = 0
    while pos < len(formula):
        m = _TOKEN_RE.match(formula, pos)
        if not m or m.end() == pos:
            raise ValueError(f"Formule chimique illisible à la position {pos} : « {formula} ».")
        element, count, open_paren, close_paren, close_count = m.groups()

        if element:
            n = int(count) if count else 1
            stack[-1][element] = stack[-1].get(element, 0) + n
        elif open_paren:
            stack.append({})
        elif close_paren:
            if len(stack) < 2:
                raise ValueError(f"Parenthèse fermante sans ouverture correspondante dans « {formula} ».")
            group = stack.pop()
            n = int(close_count) if close_count else 1
            for el, c in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + c * n

        pos = m.end()

    if len(stack) != 1:
        raise ValueError(f"Parenthèse non fermée dans « {formula} ».")
    return stack[0]


def parse_equation(equation_str: str) -> Tuple[List[str], List[str]]:
    """Parse 'H2 + O2 -> H2O' (ou '=', '→') en (réactifs, produits), formules brutes."""
    normalized = equation_str.replace("→", "->").replace("=", "->")
    if "->" not in normalized:
        raise ValueError("L'équation doit contenir une flèche de réaction ('->', '=', ou '→').")
    left, right = normalized.split("->", 1)

    def split_side(side: str) -> List[str]:
        compounds = [c.strip() for c in side.split("+") if c.strip()]
        if not compounds:
            raise ValueError("Un des membres de l'équation est vide.")
        cleaned = []
        for c in compounds:
            m = re.match(r"^\d+\s*(.*)$", c)
            cleaned.append(m.group(1) if m and m.group(1) else c)
        return cleaned

    return split_side(left), split_side(right)


def balance_equation(equation_str: str) -> ChemistryAnalysis:
    reactants, products = parse_equation(equation_str)
    compounds = reactants + products

    compositions = [parse_formula(c) for c in compounds]
    elements = sorted({el for comp in compositions for el in comp})
    if not elements:
        raise ValueError("Aucun élément chimique reconnu dans l'équation.")

    n_reactants = len(reactants)
    rows = []
    for el in elements:
        row = []
        for i, comp in enumerate(compositions):
            sign = 1 if i < n_reactants else -1
            row.append(sign * comp.get(el, 0))
        rows.append(row)
    M = sp.Matrix(rows)

    nullspace = M.nullspace()
    if not nullspace:
        raise ValueError(
            "Impossible d'équilibrer cette équation : aucune combinaison de coefficients "
            "positifs ne conserve tous les éléments (l'équation est peut-être chimiquement incorrecte)."
        )
    vec = nullspace[0]

    denominators = [term.q for term in vec if term != 0]
    lcm = sp.ilcm(*denominators) if denominators else 1
    int_vec = [int(term * lcm) for term in vec]

    g = 0
    for v in int_vec:
        g = sp.igcd(g, abs(v))
    if g > 1:
        int_vec = [v // g for v in int_vec]

    if any(v <= 0 for v in int_vec):
        raise ValueError(
            "L'équilibrage a produit des coefficients non tous strictement positifs : "
            "l'équation fournie est probablement chimiquement incorrecte (vérifiez les "
            "réactifs/produits)."
        )

    coefficients = int_vec

    def fmt_side(names, coeffs):
        parts = []
        for name, c in zip(names, coeffs):
            parts.append(name if c == 1 else f"{c} {name}")
        return " + ".join(parts)

    balanced = (
        f"{fmt_side(reactants, coefficients[:n_reactants])} -> "
        f"{fmt_side(products, coefficients[n_reactants:])}"
    )

    return ChemistryAnalysis(
        reactants=reactants, products=products, coefficients=coefficients,
        elements=elements, composition_matrix=M, balanced_equation=balanced,
    )
