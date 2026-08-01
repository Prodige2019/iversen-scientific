"""
Rédacteur pédagogique pour les circuits électriques simples (série ou parallèle).
"""
from sympy import latex
from .physics_circuits import CircuitAnalysis
from .models import Correction, Step


def write_circuit_correction(exercise_title, circuit_label, analysis: CircuitAnalysis) -> Correction:
    r_list = ", ".join(f"R_{{{i+1}}} = {latex(r)}\\,\\Omega" for i, r in enumerate(analysis.resistances))
    correction = Correction(exercise_title=exercise_title, function_str=circuit_label,
                             subject_line=f"Circuit {analysis.topology} : {r_list}, U = {latex(analysis.voltage)}\\,V")

    correction.add(Step(
        title="Identification du montage",
        result_latex=f"\\text{{Montage {analysis.topology}, }} n = {len(analysis.resistances)} \\text{{ résistances}}",
        explanation=(
            "Dans un montage série, le même courant traverse toutes les résistances. "
            "Dans un montage parallèle, c'est la même tension qui est appliquée aux bornes de chacune."
            if analysis.topology == "série" else
            "Dans un montage parallèle, la même tension U est appliquée aux bornes de chaque résistance ; "
            "le courant total se répartit entre les branches."
        ),
        weight=1.0,
    ))

    if analysis.topology == "série":
        formula = " + ".join(f"R_{{{i+1}}}" for i in range(len(analysis.resistances)))
        correction.add(Step(
            title="Résistance équivalente",
            result_latex=f"R_{{eq}} = {formula} = {latex(analysis.equivalent_resistance)}\\,\\Omega",
            explanation="En série, la résistance équivalente est la somme des résistances individuelles.",
            rule_recalled="R_{eq} = \\sum_i R_i \\quad \\text{(série)}",
            weight=2.0,
        ))
    else:
        formula = " + ".join(f"\\dfrac{{1}}{{R_{{{i+1}}}}}" for i in range(len(analysis.resistances)))
        correction.add(Step(
            title="Résistance équivalente",
            result_latex=f"\\dfrac{{1}}{{R_{{eq}}}} = {formula} \\quad\\Rightarrow\\quad R_{{eq}} = {latex(analysis.equivalent_resistance)}\\,\\Omega",
            explanation="En parallèle, l'inverse de la résistance équivalente est la somme des inverses des résistances individuelles.",
            rule_recalled="\\dfrac{1}{R_{eq}} = \\sum_i \\dfrac{1}{R_i} \\quad \\text{(parallèle)}",
            weight=2.0,
        ))

    correction.add(Step(
        title="Courant total (loi d'Ohm)",
        result_latex=f"I = \\dfrac{{U}}{{R_{{eq}}}} = \\dfrac{{{latex(analysis.voltage)}}}{{{latex(analysis.equivalent_resistance)}}} = {latex(analysis.total_current)}\\,A",
        explanation="La loi d'Ohm appliquée au circuit complet (U et la résistance équivalente) donne le courant délivré par le générateur.",
        rule_recalled="U = R \\times I",
        weight=2.0,
    ))

    detail_lines = []
    for i, (r, u, i_r, p) in enumerate(zip(analysis.resistances, analysis.voltages, analysis.currents, analysis.powers), start=1):
        detail_lines.append(f"R_{{{i}}}: U = {latex(u)}\\,V, \\ I = {latex(i_r)}\\,A, \\ P = {latex(p)}\\,W")
    correction.add(Step(
        title="Tension, courant et puissance de chaque résistance",
        result_latex=" \\qquad ".join(detail_lines),
        explanation=(
            "En série, on connaît déjà I (le même partout) : on en déduit U_i = R_i × I pour chaque résistance."
            if analysis.topology == "série" else
            "En parallèle, U est la même aux bornes de chaque résistance ; on calcule I_i = U/R_i pour chacune, "
            "puis la puissance P_i = U_i × I_i."
        ),
        rule_recalled="P = U \\times I",
        weight=2.5,
    ))

    correction.add(Step(
        title="Puissance totale dissipée",
        result_latex=f"P_{{totale}} = U \\times I = {latex(analysis.total_power)}\\,W",
        explanation="La puissance totale dissipée dans le circuit est le produit de la tension du générateur par le courant total qu'il délivre — elle doit être égale à la somme des puissances individuelles (garde-fou de cohérence).",
        weight=1.5,
    ))

    correction.compute_score()
    return correction
