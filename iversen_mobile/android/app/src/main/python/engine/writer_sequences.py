"""
Rédacteur pédagogique pour l'étude de suites définies par récurrence.
"""
import re
import sympy as sp
from sympy import latex
from .sequences import SequenceAnalysis
from .models import Correction, Step


def _display_recurrence(recurrence_str: str) -> str:
    """Affiche 'u' comme 'u_n' pour la lisibilité (n'affecte pas le parsing, seulement l'affichage)."""
    return re.sub(r"\bu\b", "u_n", recurrence_str)


def write_sequence_correction(exercise_title: str, first_term_str: str, recurrence_str: str,
                               analysis: SequenceAnalysis) -> Correction:
    subject = f"u_{{{analysis.start_index}}} = {first_term_str}, \\quad u_{{n+1}} = {_display_recurrence(recurrence_str)}"
    correction = Correction(exercise_title=exercise_title, function_str=f"{first_term_str}, {recurrence_str}",
                             subject_line=f"Suite : ${subject}$")

    terms_str = ", ".join(f"u_{{{analysis.start_index+i}}} = {latex(t)}" for i, t in enumerate(analysis.first_terms))
    correction.add(Step(
        title="Calcul des premiers termes",
        result_latex=terms_str,
        explanation="On calcule quelques termes en appliquant la relation de récurrence de proche en proche, pour observer le comportement de la suite avant toute démonstration.",
        weight=1.0,
    ))

    if analysis.kind == "non reconnue":
        correction.add(Step(
            title="Nature de la suite",
            result_latex="\\text{récurrence non affine}",
            explanation=(
                "La relation u_{n+1} = f(u_n) n'est ni de la forme u_n + r (arithmétique) "
                "ni a·u_n (géométrique) ni a·u_n + b (arithmético-géométrique) : il n'existe "
                "pas de méthode générale automatique pour en déduire une formule explicite. "
                "L'étude doit se faire au cas par cas (étude de fonction associée, etc.)."
            ),
            weight=2.0,
        ))
        correction.compute_score()
        return correction

    if analysis.kind == "arithmétique":
        correction.add(Step(
            title="Nature : suite arithmétique",
            result_latex=f"u_{{n+1}} - u_n = {latex(analysis.common_difference)} \\quad \\text{{(constant)}}",
            explanation="La différence entre deux termes consécutifs est constante : c'est la définition d'une suite arithmétique, de raison r.",
            rule_recalled="\\text{(suite arithmétique)} \\iff u_{n+1} - u_n = r \\text{ constant}",
            weight=2.0,
        ))
        correction.add(Step(
            title="Terme général",
            result_latex=f"u_n = u_{{{analysis.start_index}}} + (n - {analysis.start_index}) \\times r = {latex(analysis.general_term)}",
            explanation="Le terme général d'une suite arithmétique s'exprime directement à partir du premier terme et de la raison.",
            rule_recalled="u_n = u_{n_0} + (n-n_0)\\,r",
            weight=2.0,
        ))

    elif analysis.kind == "géométrique":
        correction.add(Step(
            title="Nature : suite géométrique",
            result_latex=f"\\dfrac{{u_{{n+1}}}}{{u_n}} = {latex(analysis.common_ratio)} \\quad \\text{{(constant)}}",
            explanation="Le rapport entre deux termes consécutifs est constant : c'est la définition d'une suite géométrique, de raison q.",
            rule_recalled="\\text{(suite géométrique)} \\iff u_{n+1} = q \\, u_n,\\ q \\text{ constant}",
            weight=2.0,
        ))
        correction.add(Step(
            title="Terme général",
            result_latex=f"u_n = u_{{{analysis.start_index}}} \\times q^{{\\,n-{analysis.start_index}}} = {latex(analysis.general_term)}",
            explanation="Le terme général d'une suite géométrique s'exprime directement à partir du premier terme et de la raison.",
            rule_recalled="u_n = u_{n_0} \\, q^{\\,n-n_0}",
            weight=2.0,
        ))

    else:  # arithmético-géométrique
        correction.add(Step(
            title="Nature : suite arithmético-géométrique",
            result_latex=f"u_{{n+1}} = {latex(analysis.a)}\\,u_n + {latex(analysis.b)}",
            explanation=(
                "La relation est affine (u_{n+1} = a·u_n + b) sans être ni purement "
                "arithmétique (a ≠ 1) ni purement géométrique (b ≠ 0) : on parle de suite "
                "arithmético-géométrique. La méthode consiste à trouver le point fixe L de "
                "la relation, puis à montrer que (u_n - L) est géométrique."
            ),
            weight=1.5,
        ))
        correction.add(Step(
            title="Point fixe",
            result_latex=f"L = a L + b \\quad\\Rightarrow\\quad L = \\dfrac{{b}}{{1-a}} = {latex(analysis.fixed_point)}",
            explanation="Le point fixe L vérifie L = a·L + b : c'est la valeur vers laquelle (u_n - L) va se comporter comme une suite géométrique pure.",
            rule_recalled="L = \\dfrac{b}{1-a} \\quad (a \\neq 1)",
            weight=1.5,
        ))
        correction.add(Step(
            title="Suite auxiliaire géométrique",
            result_latex=f"v_n = u_n - L \\quad\\Rightarrow\\quad v_n = ({latex(analysis.first_term - analysis.fixed_point)})\\times {latex(analysis.a)}^{{\\,n-{analysis.start_index}}}",
            explanation="On pose v_n = u_n - L ; v_n est alors géométrique de raison a, ce qui permet d'en déduire une formule explicite.",
            weight=1.5,
        ))
        correction.add(Step(
            title="Terme général de u_n",
            result_latex=f"u_n = v_n + L = {latex(analysis.general_term)}",
            explanation="On revient à u_n en ajoutant L à l'expression de v_n trouvée à l'étape précédente.",
            weight=1.5,
        ))

    if analysis.limit_exists and analysis.limit is not None:
        correction.add(Step(
            title="Limite quand n → +∞",
            result_latex=f"\\lim_{{n \\to +\\infty}} u_n = {latex(analysis.limit)}",
            explanation="On détermine le comportement de u_n lorsque n devient très grand, à partir de la formule du terme général.",
            weight=1.5,
        ))
    elif not analysis.limit_exists:
        correction.add(Step(
            title="Limite quand n → +∞",
            result_latex="\\text{pas de limite (suite divergente par oscillation)}",
            explanation="La raison étant négative et de valeur absolue supérieure ou égale à 1, les termes changent de signe indéfiniment sans se stabiliser : la suite n'a pas de limite.",
            weight=1.5,
        ))

    if analysis.monotonicity:
        correction.add(Step(
            title="Monotonie",
            result_latex=f"\\text{{suite {analysis.monotonicity}}}",
            explanation="On caractérise le sens de variation de la suite à partir du signe de la raison (et du signe du premier terme si nécessaire).",
            weight=1.0,
        ))

    correction.compute_score()
    return correction
