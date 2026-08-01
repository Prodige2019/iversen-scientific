"""
Rendu d'une chaîne LaTeX (telle que produite par SymPy dans les Step du moteur)
en image PNG, via matplotlib mathtext — pas de dépendance à une installation LaTeX
complète (non disponible/inutile ici), donc pas de couverture à 100% de LaTeX, mais
large sur les besoins réels du projet (fractions, exposants, racines, sommes, etc.).

Repli honnête : si mathtext ne sait pas interpréter une commande, on retente en
« nettoyant » les commandes les plus exotiques (\\text, \\mathbb, \\varnothing, \\iff,
...) plutôt que de faire planter tout l'export PDF pour une seule formule.
"""
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

_SIMPLIFICATIONS = [
    (r"\\text\{([^}]*)\}", r"\\mathrm{\1}"),   # \text{...} -> \mathrm{...} (mathtext ne supporte pas \text)
    (r"\\mathbb\{R\}", "R"),                     # pas de police blackboard bold dans mathtext
    (r"\\varnothing", r"\\emptyset"),
    (r"\\iff", r"\\Leftrightarrow"),
    (r"\\qquad", r"\\quad"),
]


def _clean_for_mathtext(latex_str: str) -> str:
    cleaned = latex_str
    for pattern, repl in _SIMPLIFICATIONS:
        cleaned = re.sub(pattern, repl, cleaned)
    return cleaned


def render_latex_to_png(latex_str: str, output_path: str, fontsize: int = 15) -> bool:
    """Rend une formule LaTeX en PNG à fond transparent. Renvoie True si le rendu
    mathématique a réussi, False si on est retombé sur un rendu texte brut (dans
    les deux cas un fichier PNG utilisable est produit — jamais d'exception levée
    vers l'appelant, l'export PDF ne doit jamais planter pour une formule)."""
    for candidate in (latex_str, _clean_for_mathtext(latex_str)):
        try:
            fig = plt.figure(figsize=(0.1, 0.1))
            fig.text(0, 0, f"${candidate}$", fontsize=fontsize, color="#1B2A45")
            fig.savefig(output_path, bbox_inches="tight", dpi=200, transparent=True, pad_inches=0.05)
            plt.close(fig)
            return True
        except Exception:
            plt.close("all")
            continue

    # dernier repli : texte brut sans rendu mathématique (retire les commandes LaTeX
    # de façon grossière), pour ne jamais faire échouer l'export entier
    plain = re.sub(r"\\[a-zA-Z]+", " ", latex_str).replace("{", "").replace("}", "")
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.text(0, 0, plain, fontsize=fontsize, color="#1B2A45")
    fig.savefig(output_path, bbox_inches="tight", dpi=200, transparent=True, pad_inches=0.05)
    plt.close(fig)
    return False
