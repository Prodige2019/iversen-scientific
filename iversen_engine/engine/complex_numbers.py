"""
Moteur d'étude d'un nombre complexe — forme algébrique, module, argument,
formes trigonométrique et exponentielle, conjugué. Calcul exact via SymPy
(fractions, pi exact) quand possible, décimal en repli.
"""
from dataclasses import dataclass
from tokenize import TokenError
import sympy as sp
from .equations import parse_math_expression


@dataclass
class ComplexAnalysis:
    z: sp.Expr
    re: sp.Expr
    im: sp.Expr
    modulus: sp.Expr
    argument: sp.Expr              # dans ]-π, π]
    argument_is_notable: bool      # True si l'argument est un multiple simple de π (angle remarquable)
    conjugate: sp.Expr
    trig_form: str                 # texte LaTeX "r(cos θ + i sin θ)"
    exp_form: str                  # texte LaTeX "r e^{iθ}"


_NOTABLE_ANGLES = {
    sp.pi / 6, sp.pi / 4, sp.pi / 3, sp.pi / 2, 2 * sp.pi / 3, 3 * sp.pi / 4, 5 * sp.pi / 6, sp.pi,
    -sp.pi / 6, -sp.pi / 4, -sp.pi / 3, -sp.pi / 2, -2 * sp.pi / 3, -3 * sp.pi / 4, -5 * sp.pi / 6, sp.Integer(0),
}


def parse_complex(z_str: str) -> sp.Expr:
    try:
        z = parse_math_expression(z_str.strip(), {"I": sp.I, "i": sp.I, "j": sp.I})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Nombre complexe illisible : « {z_str} ». Détail : {e}")
    real_free = z.free_symbols
    if real_free:
        raise ValueError(f"« {z_str} » doit être un nombre complexe constant, pas une expression avec variable(s) : {real_free}.")
    return sp.simplify(z)


def analyze_complex(z_str: str) -> ComplexAnalysis:
    z = parse_complex(z_str)

    if z == 0:
        raise ValueError(
            "Le nombre 0 n'a pas d'argument défini (module nul) — l'étude de forme "
            "trigonométrique/exponentielle ne s'applique pas."
        )

    re = sp.re(z)
    im = sp.im(z)
    modulus = sp.simplify(sp.Abs(z))
    argument = sp.simplify(sp.arg(z))
    conj = sp.conjugate(z)

    is_notable = False
    if argument == 0 or argument.has(sp.pi):
        try:
            is_notable = sp.nsimplify(argument, [sp.pi]) in _NOTABLE_ANGLES
        except Exception:
            is_notable = False

    trig_form = f"{sp.latex(modulus)} \\left( \\cos\\left({sp.latex(argument)}\\right) + i \\sin\\left({sp.latex(argument)}\\right) \\right)"
    exp_form = f"{sp.latex(modulus)} \\, e^{{i {sp.latex(argument)}}}"

    return ComplexAnalysis(
        z=z, re=re, im=im, modulus=modulus, argument=argument,
        argument_is_notable=bool(is_notable), conjugate=conj,
        trig_form=trig_form, exp_form=exp_form,
    )
