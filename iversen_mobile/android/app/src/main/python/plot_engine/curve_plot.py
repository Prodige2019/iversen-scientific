"""
Moteur de tracé de courbes — réutilise directement les résultats déjà calculés par
engine.functions.analyze() (extremums, points d'inflexion, asymptotes, domaine) pour
annoter le graphique, plutôt que de refaire une analyse séparée : un seul calcul,
deux usages (correction rédigée + graphique).

Esthétique « feuille de cahier » : fond crème, grille bleu clair, axes et courbe en
encre bleu-nuit — cohérente avec le reste de l'identité visuelle du projet.
"""
import io
from typing import Optional, Tuple

import numpy as np
import sympy as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from engine.functions import FunctionAnalysis, x

PAPER = "#FAF6EE"
GRID = "#C9D9E8"
INK = "#1B2A45"
RED = "#B23A2F"
GREEN = "#3E7A52"


def _auto_range(analysis: FunctionAnalysis) -> Tuple[float, float]:
    """Détermine une fenêtre d'affichage raisonnable à partir des points caractéristiques
    déjà calculés (extremums, inflexions) — pas d'un choix arbitraire fixe."""
    xs = [float(cp.x0) for cp in analysis.critical_points if cp.x0.is_real]
    xs += [float(ip.x0) for ip in analysis.inflection_points if ip.x0.is_real]

    if xs:
        lo, hi = min(xs), max(xs)
        pad = max(2.0, (hi - lo) * 0.8 + 1.0)
        return lo - pad, hi + pad
    return -10.0, 10.0


def _domain_mask(x_vals: np.ndarray, domain: sp.Set) -> np.ndarray:
    """Masque (booléen) des points de x_vals qui appartiennent réellement au domaine
    de définition — évite de tracer une courbe là où f n'est pas définie."""
    mask = np.ones_like(x_vals, dtype=bool)
    try:
        if domain is sp.S.Reals:
            return mask
        for i, v in enumerate(x_vals):
            mask[i] = bool(domain.contains(sp.Float(v)))
    except Exception:
        pass
    return mask


def plot_function_analysis(
    analysis: FunctionAnalysis,
    expr_str: str,
    output_path: str,
    x_range: Optional[Tuple[float, float]] = None,
    figsize: Tuple[float, float] = (7.5, 6.0),
) -> None:
    """Génère un PNG du graphe de la fonction, annoté avec les points caractéristiques
    déjà calculés par le moteur de correction. Ne lève jamais d'exception pour une
    fonction non traçable numériquement : produit alors un graphique vide annoté
    plutôt que de faire planter l'appelant (cohérent avec le reste du projet)."""
    x_lo, x_hi = x_range or _auto_range(analysis)

    f_num = sp.lambdify(x, analysis.expr, modules=["numpy"])

    n_points = 2000
    x_vals = np.linspace(x_lo, x_hi, n_points)
    mask = _domain_mask(x_vals, analysis.domain)

    with np.errstate(all="ignore"):
        try:
            y_vals = f_num(x_vals)
            y_vals = np.asarray(y_vals, dtype=float)
        except Exception:
            y_vals = np.full_like(x_vals, np.nan)

    y_vals = np.where(mask, y_vals, np.nan)
    finite = y_vals[np.isfinite(y_vals)]

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    if finite.size > 0:
        y_lo, y_hi = np.percentile(finite, [2, 98])
        y_pad = max(1.0, (y_hi - y_lo) * 0.25)
        y_lo, y_hi = y_lo - y_pad, y_hi + y_pad
        y_plot = np.where((y_vals > y_lo - (y_hi - y_lo)) & (y_vals < y_hi + (y_hi - y_lo)), y_vals, np.nan)
        ax.plot(x_vals, y_plot, color=INK, linewidth=2.2, solid_capstyle="round")
        ax.set_ylim(y_lo, y_hi)
    else:
        ax.text(0.5, 0.5, "Fonction non traçable numériquement sur cette fenêtre",
                 ha="center", va="center", transform=ax.transAxes, color=RED, fontsize=11)

    ax.set_xlim(x_lo, x_hi)

    ax.grid(True, color=GRID, linewidth=0.9)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(mticker.MultipleLocator(max(1, round((ax.get_ylim()[1] - ax.get_ylim()[0]) / 10) or 1)))
    ax.axhline(0, color=INK, linewidth=1.4)
    ax.axvline(0, color=INK, linewidth=1.4)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=INK, labelsize=8)

    for asym in analysis.asymptotes:
        if asym.kind == "verticale":
            try:
                x0 = float(sp.sympify(asym.description.split("=")[1].strip(), locals={"pi": sp.pi}))
                if x_lo <= x0 <= x_hi:
                    ax.axvline(x0, color=RED, linewidth=1.2, linestyle="--", alpha=0.8)
            except Exception:
                pass
        elif asym.kind == "horizontale":
            try:
                y0 = float(sp.sympify(asym.description.split("=")[1].split("(")[0].strip()))
                ax.axhline(y0, color=RED, linewidth=1.2, linestyle="--", alpha=0.8)
            except Exception:
                pass

    for cp in analysis.critical_points:
        try:
            x0, y0 = float(cp.x0), float(cp.y0)
        except (TypeError, ValueError):
            continue
        if not (x_lo <= x0 <= x_hi):
            continue
        color = GREEN if "maximum" in cp.kind else (RED if "minimum" in cp.kind else INK)
        ax.plot(x0, y0, "o", color=color, markersize=6, zorder=5)
        ax.annotate(f"({x0:.2g}; {y0:.2g})", (x0, y0), textcoords="offset points",
                    xytext=(6, 8), fontsize=8, color=color)

    for ip in analysis.inflection_points:
        try:
            x0, y0 = float(ip.x0), float(ip.y0)
        except (TypeError, ValueError):
            continue
        if not (x_lo <= x0 <= x_hi):
            continue
        ax.plot(x0, y0, "D", color=INK, markersize=6, zorder=5, markerfacecolor=PAPER, markeredgewidth=1.6)
        ax.annotate("inflexion", (x0, y0), textcoords="offset points", xytext=(6, -12), fontsize=7.5, color=INK)

    ax.set_title(f"f(x) = {sp.latex(analysis.expr)}", fontsize=12, color=INK, pad=12)

    fig.tight_layout()
    fig.savefig(output_path, dpi=160, facecolor=PAPER)
    plt.close(fig)


def plot_function_analysis_data(
    analysis: FunctionAnalysis,
    expr_str: str,
    x_range: Optional[Tuple[float, float]] = None,
    n_points: int = 600,
) -> dict:
    """Même logique que plot_function_analysis() (fenêtre auto, masque de domaine,
    points caractéristiques) mais renvoie des données brutes en JSON plutôt qu'une
    image, pour un graphique interactif côté frontend (zoom, survol...).

    Un seul calcul (analyze()) est donc réutilisé pour les deux usages : image
    statique (export PDF/Word) et graphique interactif (affichage à l'écran).
    """
    x_lo, x_hi = x_range or _auto_range(analysis)

    f_num = sp.lambdify(x, analysis.expr, modules=["numpy"])

    x_vals = np.linspace(x_lo, x_hi, n_points)
    mask = _domain_mask(x_vals, analysis.domain)

    with np.errstate(all="ignore"):
        try:
            y_vals = f_num(x_vals)
            y_vals = np.asarray(y_vals, dtype=float)
            if y_vals.shape != x_vals.shape:
                # certaines fonctions constantes renvoient un scalaire au lieu
                # d'un tableau : on l'étale pour garder la même longueur que x
                y_vals = np.full_like(x_vals, float(y_vals))
        except Exception:
            y_vals = np.full_like(x_vals, np.nan)

    y_vals = np.where(mask, y_vals, np.nan)
    finite = y_vals[np.isfinite(y_vals)]

    if finite.size > 0:
        y_lo, y_hi = np.percentile(finite, [2, 98])
        y_pad = max(1.0, (y_hi - y_lo) * 0.25)
        y_lo, y_hi = y_lo - y_pad, y_hi + y_pad
        # au-delà de la fenêtre affichée, on coupe (comme la version image) pour
        # qu'une asymptote verticale ne tire pas toute la courbe hors cadre
        y_vals = np.where((y_vals > y_lo - (y_hi - y_lo)) & (y_vals < y_hi + (y_hi - y_lo)), y_vals, np.nan)
    else:
        y_lo, y_hi = -10.0, 10.0

    # JSON ne supporte pas NaN : on utilise None, que Plotly (frontend) sait déjà
    # interpréter comme un "trou" dans la courbe (segment non défini).
    y_list = [None if not np.isfinite(v) else round(float(v), 6) for v in y_vals]
    x_list = [round(float(v), 6) for v in x_vals]

    def _point(cp, extra=None):
        try:
            px, py = float(cp.x0), float(cp.y0)
        except (TypeError, ValueError):
            return None
        if not (x_lo <= px <= x_hi):
            return None
        point = {"x": round(px, 6), "y": round(py, 6)}
        if extra:
            point.update(extra)
        return point

    critical_points = []
    for cp in analysis.critical_points:
        p = _point(cp, {"kind": cp.kind})
        if p:
            critical_points.append(p)

    inflection_points = []
    for ip in analysis.inflection_points:
        p = _point(ip)
        if p:
            inflection_points.append(p)

    vertical_asymptotes = []
    horizontal_asymptotes = []
    for asym in analysis.asymptotes:
        if asym.kind == "verticale":
            try:
                x0 = float(sp.sympify(asym.description.split("=")[1].strip(), locals={"pi": sp.pi}))
                if x_lo <= x0 <= x_hi:
                    vertical_asymptotes.append(round(x0, 6))
            except Exception:
                pass
        elif asym.kind == "horizontale":
            try:
                y0 = float(sp.sympify(asym.description.split("=")[1].split("(")[0].strip()))
                horizontal_asymptotes.append(round(y0, 6))
            except Exception:
                pass

    def _dedup(values, ndigits=6):
        seen = []
        for v in values:
            if not any(abs(v - s) < 10 ** (-ndigits + 2) for s in seen):
                seen.append(v)
        return seen

    return {
        "x": x_list,
        "y": y_list,
        "x_range": [round(x_lo, 6), round(x_hi, 6)],
        "y_range": [round(float(y_lo), 6), round(float(y_hi), 6)],
        "critical_points": critical_points,
        "inflection_points": inflection_points,
        "vertical_asymptotes": _dedup(vertical_asymptotes),
        "horizontal_asymptotes": _dedup(horizontal_asymptotes),
        "expr_display": sp.latex(analysis.expr),
    }


def plot_function_analysis_bytes(analysis: FunctionAnalysis, expr_str: str, **kwargs) -> bytes:
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name
    try:
        plot_function_analysis(analysis, expr_str, path, **kwargs)
        with open(path, "rb") as f:
            data = f.read()
    finally:
        os.unlink(path)
    return data
