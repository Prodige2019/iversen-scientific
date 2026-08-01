"""
Rédacteur pédagogique — transforme les résultats du moteur symbolique (engine.functions)
en une correction rédigée façon copie d'examen, en français.

Aucun appel LLM ici : uniquement des templates conditionnels. C'est volontaire pour
la Phase 1 : la rédaction reste garantie fidèle aux calculs, sans risque d'hallucination.
Un point d'extension (engine.llm_bridge) permettra plus tard d'enrichir le *phrasé*
sans jamais modifier les résultats mathématiques eux-mêmes.
"""
import sympy as sp
from sympy import latex
from .functions import FunctionAnalysis, x
from .models import Correction, Step


def _fmt(expr: sp.Expr) -> str:
    return latex(sp.nsimplify(expr)) if expr.is_number else latex(expr)


def write_correction(exercise_title: str, function_str: str, analysis: FunctionAnalysis) -> Correction:
    correction = Correction(exercise_title=exercise_title, function_str=function_str)

    if analysis.study_window_note:
        correction.add(Step(
            title="Remarque préalable",
            result_latex="\\text{fenêtre d'étude} : [-2\\pi, 2\\pi]",
            explanation=analysis.study_window_note,
            weight=0.0,  # purement informatif, ne compte pas dans la note
        ))

    # Étape 1 — domaine de définition
    correction.add(Step(
        title="Ensemble de définition",
        result_latex=f"D_f = {latex(analysis.domain)}",
        explanation=(
            "On détermine les valeurs de x pour lesquelles l'expression de f est calculable "
            "(pas de division par zéro, pas de racine d'un nombre négatif, pas de logarithme "
            "d'une valeur négative ou nulle)."
        ),
        weight=1.5,
    ))

    # Étape 2 — parité (seulement si pertinent, i.e. domaine symétrique probable)
    if analysis.parity.startswith("non pertinente"):
        correction.add(Step(
            title="Parité",
            result_latex="\\text{étude de parité non pertinente}",
            explanation=(
                "Le domaine de définition n'est pas symétrique par rapport à 0 : "
                "la question de la parité ne se pose donc pas ici."
            ),
            weight=0.5,
        ))
    else:
        correction.add(Step(
            title="Parité",
            result_latex=f"f \\text{{ est { analysis.parity }}}",
            explanation=(
                "On compare f(-x) à f(x) : si f(-x) = f(x), f est paire (courbe symétrique par "
                "rapport à l'axe des ordonnées) ; si f(-x) = -f(x), f est impaire (symétrie par "
                "rapport à l'origine)."
            ),
            rule_recalled="f paire ⇔ f(-x) = f(x)    f impaire ⇔ f(-x) = -f(x)",
            weight=0.5,
        ))

    # Étape 3 — dérivée
    correction.add(Step(
        title="Calcul de la dérivée",
        result_latex=f"f'(x) = {latex(analysis.derivative)}",
        explanation="On dérive f terme à terme en appliquant les règles usuelles de dérivation.",
        rule_recalled="(x^n)' = n\\,x^{n-1} \\quad (u+v)' = u' + v' \\quad (uv)' = u'v + uv'",
        weight=2.0,  # compétence centrale de l'exercice
    ))

    # Étape 4 — signe de la dérivée / variations
    if analysis.sign_intervals:
        sign_desc = "  ·  ".join(
            f"{sp.pretty(interval)} : f' {sign} 0" for interval, sign in analysis.sign_intervals
        )
    else:
        sign_desc = "\\text{signe non déterminé automatiquement sur ce domaine}"
    correction.add(Step(
        title="Étude du signe de f' et variations",
        result_latex=sign_desc,
        explanation=(
            "Le signe de f' donne le sens de variation de f : f est croissante là où f' est "
            "positive, décroissante là où f' est négative."
        ),
        rule_recalled="f' > 0 sur I ⇒ f croissante sur I    f' < 0 sur I ⇒ f décroissante sur I",
        weight=2.0,  # compétence centrale de l'exercice
    ))

    # Étape 5 — extrema
    if analysis.critical_points:
        details = "  ·  ".join(
            f"{cp.kind} en x = {latex(cp.x0)}, f({latex(cp.x0)}) = {latex(cp.y0)}"
            for cp in analysis.critical_points
        )
        correction.add(Step(
            title="Extremums locaux",
            result_latex=details,
            explanation=(
                "Un extremum local apparaît là où f' s'annule en changeant de signe : "
                "f' passe de + à - pour un maximum, de - à + pour un minimum."
            ),
            weight=1.5,
        ))
    else:
        correction.add(Step(
            title="Extremums locaux",
            result_latex="Aucun extremum local",
            explanation="f' ne s'annule en changeant de signe en aucun point : f est strictement monotone (ou constante par morceaux).",
            weight=1.5,
        ))

    # Étape 6 — point(s) d'inflexion
    if analysis.inflection_points:
        details = "  ·  ".join(
            f"({latex(ip.x0)}, {latex(ip.y0)})" for ip in analysis.inflection_points
        )
        correction.add(Step(
            title="Point(s) d'inflexion",
            result_latex=f"f''(x) = {latex(analysis.second_derivative)} \\quad \\Rightarrow \\quad {details}",
            explanation=(
                "Un point d'inflexion correspond à un changement de convexité, c'est-à-dire "
                "à un zéro de f'' où f'' change effectivement de signe (une simple annulation "
                "sans changement de signe ne suffit pas)."
            ),
            warning="Erreur fréquente : conclure à un point d'inflexion dès que f''(x0) = 0, "
                    "sans vérifier le changement de signe de f''.",
            weight=1.5,
        ))
    else:
        correction.add(Step(
            title="Point(s) d'inflexion",
            result_latex=f"f''(x) = {latex(analysis.second_derivative)} \\quad \\Rightarrow \\quad \\text{{aucun}}",
            explanation="f'' ne change pas de signe sur le domaine : la courbe ne change pas de convexité.",
            weight=1.5,
        ))

    # Étape 7 — limites aux bornes
    if analysis.limits_at_bounds:
        details = "  ·  ".join(
            f"\\lim_{{x \\to {b}}} f(x) = {latex(l)}" for b, l in analysis.limits_at_bounds
        )
        correction.add(Step(
            title="Limites aux bornes du domaine",
            result_latex=details,
            explanation="On étudie le comportement de f lorsque x tend vers les bornes de son ensemble de définition.",
            weight=1.0,
        ))

    # Étape 8 — asymptotes
    if analysis.asymptotes:
        details = "  ·  ".join(f"{a.kind} : {a.description}" for a in analysis.asymptotes)
        correction.add(Step(
            title="Asymptotes",
            result_latex=details,
            explanation="Une asymptote traduit le comportement de la courbe au voisinage d'un point exclu du domaine ou à l'infini.",
            weight=1.0,
        ))

    correction.compute_score()
    return correction


def render_text(correction: Correction) -> str:
    """Rendu texte brut (console / fichier .txt), façon copie corrigée."""
    lines = [
        f"═══ {correction.exercise_title} ═══",
        correction.subject_line or f"f(x) = {correction.function_str}",
        "",
    ]
    for i, step in enumerate(correction.steps, start=1):
        mark = "✓" if step.is_complete else "○"
        lines.append(f"{mark} Étape {i} — {step.title}")
        lines.append(f"    {step.result_latex}")
        lines.append(f"    {step.explanation}")
        if step.rule_recalled:
            lines.append(f"    Règle rappelée : {step.rule_recalled}")
        if step.warning:
            lines.append(f"    ⚠ {step.warning}")
        lines.append("")
    lines.append(f"Note : {correction.score}/{correction.score_max}")
    return "\n".join(lines)


def render_markdown(correction: Correction) -> str:
    """Rendu Markdown (LaTeX inline $...$) — utile pour export / affichage web."""
    lines = [
        f"# {correction.exercise_title}",
        f"**{correction.subject_line or ('f(x) = ' + correction.function_str)}**",
        "",
    ]
    for i, step in enumerate(correction.steps, start=1):
        mark = "✅" if step.is_complete else "◻️"
        lines.append(f"### {mark} Étape {i} — {step.title}")
        lines.append(f"$$ {step.result_latex} $$")
        lines.append(step.explanation)
        if step.rule_recalled:
            lines.append(f"> **Règle rappelée :** ${step.rule_recalled}$")
        if step.warning:
            lines.append(f"> ⚠️ **Attention :** {step.warning}")
        lines.append("")
    lines.append(f"**Note : {correction.score}/{correction.score_max}**")
    return "\n".join(lines)
