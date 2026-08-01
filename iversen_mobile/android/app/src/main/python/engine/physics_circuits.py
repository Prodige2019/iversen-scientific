"""
Moteur de circuits électriques simples — association de résistances en série ou
en parallèle, loi d'Ohm, calcul du courant/tension/puissance pour chaque
composant. Calcul exact via SymPy (fractions), même philosophie que le reste
du projet.

Portée volontairement limitée à un seul type d'association à la fois (toutes en
série, ou toutes en parallèle) — les réseaux mixtes série+parallèle demandent une
analyse topologique plus générale, hors périmètre de cette première itération.
"""
from dataclasses import dataclass
from typing import List
import sympy as sp
from .equations import parse_math_expression


@dataclass
class CircuitAnalysis:
    resistances: List[sp.Expr]
    topology: str
    voltage: sp.Expr
    equivalent_resistance: sp.Expr
    total_current: sp.Expr
    currents: List[sp.Expr]
    voltages: List[sp.Expr]
    powers: List[sp.Expr]
    total_power: sp.Expr


def _parse_positive(value_str: str, label: str) -> sp.Expr:
    try:
        v = sp.nsimplify(parse_math_expression(value_str))
    except (sp.SympifyError, TypeError) as e:
        raise ValueError(f"Valeur illisible pour {label} : « {value_str} ». Détail : {e}")
    if not (v.is_real and v > 0):
        raise ValueError(f"{label} doit être un nombre strictement positif (reçu : {v}).")
    return v


def analyze_circuit(resistance_strs: List[str], topology: str, voltage_str: str) -> CircuitAnalysis:
    if not resistance_strs:
        raise ValueError("Il faut au moins une résistance.")
    if topology not in ("série", "parallèle"):
        raise ValueError(f"Topologie inconnue : « {topology} » (attendu : « série » ou « parallèle »).")

    resistances = [_parse_positive(r, f"R{i+1}") for i, r in enumerate(resistance_strs)]
    voltage = _parse_positive(voltage_str, "U")

    if topology == "série":
        req = sp.simplify(sum(resistances))
        total_current = sp.simplify(voltage / req)
        currents = [total_current] * len(resistances)
        voltages = [sp.simplify(total_current * r) for r in resistances]
    else:
        req = sp.simplify(1 / sum(1 / r for r in resistances))
        total_current = sp.simplify(voltage / req)
        voltages = [voltage] * len(resistances)
        currents = [sp.simplify(voltage / r) for r in resistances]

    powers = [sp.simplify(v * i) for v, i in zip(voltages, currents)]
    total_power = sp.simplify(sum(powers))

    return CircuitAnalysis(
        resistances=resistances, topology=topology, voltage=voltage,
        equivalent_resistance=req, total_current=total_current,
        currents=currents, voltages=voltages, powers=powers, total_power=total_power,
    )
