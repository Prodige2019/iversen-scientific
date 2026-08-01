"""
Moteur de calcul symbolique — 100% déterministe, basé sur SymPy (open-source, offline).
Ne dépend d'aucun LLM. C'est la source de vérité mathématique.

Couverture : polynômes, fractions rationnelles, exponentielle, logarithme, et
fonctions trigonométriques (sin/cos/tan) sur une fenêtre d'étude bornée (les
fonctions périodiques ont une infinité de points caractéristiques ; on étudie
une fenêtre représentative et on le signale explicitement dans la correction).
"""
from tokenize import TokenError
from dataclasses import dataclass
from typing import List, Optional, Tuple
import sympy as sp
from sympy.calculus.util import continuous_domain
from sympy import S, oo, latex, solveset, Interval, Union, FiniteSet, EmptySet
from .equations import normalize_variable_case, parse_math_expression

x = sp.symbols("x", real=True)

# Fenêtre d'étude par défaut pour les fonctions périodiques (sin, cos, tan, ...)
# dont le domaine ou les points caractéristiques (zéros de f' ou f'') sont en
# nombre infini. On documente ce choix dans la correction plutôt que de le cacher.
TRIG_ATOMS = {sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc}
DEFAULT_TRIG_WINDOW = Interval(-2 * sp.pi, 2 * sp.pi)


@dataclass
class CriticalPoint:
    x0: sp.Expr
    y0: sp.Expr
    kind: str  # "maximum local", "minimum local", "point stationnaire", ou variante "(point anguleux)"
    is_angular: bool = False


@dataclass
class InflectionPoint:
    x0: sp.Expr
    y0: sp.Expr


@dataclass
class Asymptote:
    kind: str          # "verticale" | "horizontale" | "oblique"
    description: str   # texte prêt à insérer, ex: "x = 1" ou "y = 2x + 1"


@dataclass
class FunctionAnalysis:
    expr: sp.Expr
    domain: sp.Set
    parity: str
    derivative: sp.Expr
    second_derivative: sp.Expr
    sign_intervals: List[Tuple[sp.Set, str]]
    critical_points: List[CriticalPoint]
    inflection_points: List[InflectionPoint]
    asymptotes: List[Asymptote]
    limits_at_bounds: List[Tuple[str, sp.Expr]]
    study_window_note: Optional[str] = None  # renseigné si l'analyse a été bornée (fonctions périodiques)


def parse_function(expr_str: str) -> sp.Expr:
    """Parse une chaîne en expression SymPy. Lève une erreur claire si invalide."""
    try:
        # `locals={"x": x}` est essentiel : sans cela, sympify crée un symbole "x"
        # générique distinct de celui utilisé partout ailleurs dans le moteur,
        # et toutes les dérivées calculées ensuite seraient silencieusement nulles.
        return parse_math_expression(normalize_variable_case(expr_str), {"x": x})
    except (sp.SympifyError, TypeError, SyntaxError, TokenError) as e:
        raise ValueError(f"Expression illisible : « {expr_str} ». Détail : {e}")


def compute_domain(expr: sp.Expr) -> sp.Set:
    try:
        return continuous_domain(expr, x, S.Reals)
    except NotImplementedError:
        # repli prudent : on ne sait pas déterminer le domaine automatiquement
        return S.Reals


def compute_parity(expr: sp.Expr, domain: sp.Set) -> str:
    # la parité n'a de sens que sur un domaine symétrique par rapport à 0
    if not _is_domain_symmetric(domain):
        return "non pertinente ici (domaine non symétrique)"
    f_minus_x = sp.simplify(expr.subs(x, -x))
    if sp.simplify(f_minus_x - expr) == 0:
        return "paire"
    if sp.simplify(f_minus_x + expr) == 0:
        return "impaire"
    return "aucune parité particulière"


def _is_domain_symmetric(domain: sp.Set) -> bool:
    """Teste si le domaine est symétrique par rapport à 0 (condition nécessaire
    pour que la question de la parité ait un sens)."""
    if domain is S.Reals or domain == Interval(-oo, oo):
        return True
    pieces = _domain_pieces(domain)
    mirrored = Union(*[Interval(-p.end if p.end != oo else oo,
                                 -p.start if p.start != -oo else -oo,
                                 left_open=p.right_open, right_open=p.left_open)
                        for p in pieces]) if pieces else S.EmptySet
    try:
        return domain == mirrored or sp.simplify(domain.symmetric_difference(mirrored)) == S.EmptySet
    except Exception:
        return False


def is_periodic_expr(expr: sp.Expr) -> bool:
    return any(atom.func in TRIG_ATOMS for atom in expr.atoms(sp.Function))


def compute_study_domain(domain: sp.Set, expr: sp.Expr) -> Tuple[sp.Set, Optional[str]]:
    """Restreint le domaine de RECHERCHE des points caractéristiques (zéros de f', f'')
    à une fenêtre bornée quand la fonction est périodique — sinon il y a une infinité
    de solutions et on ne peut pas toutes les lister. Le domaine de DÉFINITION affiché
    à l'élève, lui, reste inchangé (non borné)."""
    if is_periodic_expr(expr):
        window = domain.intersect(DEFAULT_TRIG_WINDOW)
        note = (
            "Fonction périodique : l'étude des variations et des points caractéristiques "
            "est menée sur la fenêtre représentative [-2π, 2π] ; le comportement se répète "
            "ensuite à l'identique par périodicité."
        )
        return window, note
    return domain, None


def _domain_pieces(domain: sp.Set) -> List[sp.Interval]:
    """Décompose un domaine (Interval, Union d'Interval, S.Reals...) en morceaux
    continus (des Interval), pour ne chercher/échantillonner qu'à l'intérieur.
    Ne renvoie JAMAIS un morceau non borné pour un domaine qu'on ne sait pas
    décomposer précisément (ex: Complement périodique de tan) : chercher des
    zéros sur (-oo, oo) pour une fonction périodique ferait itérer SymPy sur un
    ensemble de solutions infini et bloquerait le moteur."""
    if domain is S.Reals or domain == Interval(-oo, oo):
        return [Interval(-oo, oo)]
    if isinstance(domain, Interval):
        return [domain]
    if isinstance(domain, Union):
        pieces = [p for p in domain.args if isinstance(p, Interval)]
        if pieces:
            return sorted(pieces, key=lambda p: float(p.start) if p.start.is_finite else -1e18)
    if isinstance(domain, sp.Complement) and domain.args:
        universe = domain.args[0]
        if isinstance(universe, Interval):
            return [universe]
    if domain is EmptySet:
        return []
    # repli prudent : domaine trop complexe pour être décomposé exactement
    # (ex: fonction périodique sans fenêtre d'étude déjà appliquée). On se
    # borne à la fenêtre d'étude par défaut plutôt qu'à (-oo, oo), pour ne
    # jamais risquer une itération sur un ensemble de solutions infini.
    return [DEFAULT_TRIG_WINDOW]


def _safe_zeros_in(expr: sp.Expr, piece: sp.Interval) -> List[sp.Expr]:
    """Cherche les zéros de `expr` à l'intérieur de `piece`, en tolérant les cas
    où SymPy ne trouve pas de forme fermée (fonctions transcendantes complexes) :
    on renvoie alors une liste vide plutôt que de planter. IMPORTANT : on ne fait
    JAMAIS `for z in result` sur autre chose qu'un FiniteSet — un Union d'ImageSet
    (solutions périodiques infinies) bloquerait le processus indéfiniment."""
    try:
        result = solveset(sp.Eq(expr, 0), x, domain=piece)
    except Exception:
        return []
    if not isinstance(result, FiniteSet):
        # ConditionSet, ImageSet, Union d'ImageSet (périodique), etc. : on ne
        # tente pas de les énumérer, par sécurité (risque de boucle infinie).
        return []
    try:
        zeros = [z for z in result if z.is_real]
    except TypeError:
        return []
    return sorted(zeros, key=lambda z: float(z))


def find_breakpoints(expr: sp.Expr, domain: sp.Set) -> List[sp.Expr]:
    """Repère les points où f n'est structurellement pas dérivable de façon lisse :
    les zéros des arguments de valeur absolue, et les bornes des morceaux d'un
    Piecewise. Ce sont les candidats à un « point anguleux »."""
    points = set()

    for abs_term in expr.atoms(sp.Abs):
        arg = abs_term.args[0]
        try:
            zeros = solveset(sp.Eq(arg, 0), x, domain=S.Reals)
            if isinstance(zeros, FiniteSet):
                points.update(z for z in zeros if z.is_real)
        except Exception:
            pass

    for pw in expr.atoms(sp.Piecewise):
        for _, cond in pw.args:
            if cond is sp.true or cond is sp.false:
                continue
            try:
                for rel in cond.atoms(sp.core.relational.Relational):
                    lhs, rhs = rel.lhs, rel.rhs
                    if lhs == x and rhs.is_number:
                        points.add(rhs)
                    elif rhs == x and lhs.is_number:
                        points.add(lhs)
            except Exception:
                continue

    real_points = [p for p in points if p.is_real]
    try:
        real_points = [p for p in real_points if domain.contains(p) == True]  # noqa: E712
    except Exception:
        pass
    return sorted(real_points, key=lambda z: float(z))


def has_non_smooth_structure(expr: sp.Expr) -> bool:
    return bool(expr.atoms(sp.Abs)) or bool(expr.atoms(sp.Piecewise))


def _sample_point(a: sp.Expr, b: sp.Expr) -> float:
    """Choisit un point d'échantillonnage strictement entre a et b (bornes possiblement infinies)."""
    if a == -oo and b == oo:
        return 0.0
    if a == -oo:
        return float(b) - 1.0
    if b == oo:
        return float(a) + 1.0
    return (float(a) + float(b)) / 2.0


def compute_sign_intervals(expr: sp.Expr, search_domain: sp.Set, extra_breakpoints: Optional[List[sp.Expr]] = None) -> List[Tuple[sp.Set, str]]:
    """Détermine le signe de `expr` par intervalles, uniquement à l'intérieur du
    domaine de recherche fourni (fondamental pour les fonctions non définies partout,
    ex: 1/x autour de 0). `extra_breakpoints` permet d'imposer une coupure là où la
    fonction change de définition (Abs, Piecewise) même si l'expression n'y vaut pas
    zéro à proprement parler (ex: changement de pente sans passage par zéro)."""
    extra_breakpoints = extra_breakpoints or []
    intervals: List[Tuple[sp.Set, str]] = []
    for piece in _domain_pieces(search_domain):
        zeros = _safe_zeros_in(expr, piece)
        cuts = {b for b in extra_breakpoints if piece.contains(b) == True}  # noqa: E712
        bounds = [piece.start] + sorted(set(zeros) | cuts, key=lambda z: float(z)) + [piece.end]
        for i in range(len(bounds) - 1):
            a, b = bounds[i], bounds[i + 1]
            if a == b:
                continue
            sample = _sample_point(a, b)
            try:
                val = expr.subs(x, sample)
                val = complex(val)
                if abs(val.imag) > 1e-9:
                    continue  # point hors du domaine réel de la fonction, on l'ignore
                val = val.real
            except (TypeError, ValueError):
                continue
            sign = "+" if val > 1e-12 else ("-" if val < -1e-12 else "0")
            intervals.append((Interval(a, b), sign))
    return intervals


def compute_critical_points(expr: sp.Expr, derivative: sp.Expr, search_domain: sp.Set) -> List[CriticalPoint]:
    points = []
    breakpoints = set(find_breakpoints(expr, search_domain))
    for piece in _domain_pieces(search_domain):
        smooth_zeros = set(_safe_zeros_in(derivative, piece))
        piece_breakpoints = {b for b in breakpoints if piece.contains(b) == True}  # noqa: E712
        candidates = sorted(smooth_zeros | piece_breakpoints, key=lambda z: float(z))
        for z in candidates:
            eps = 1e-3
            try:
                before_val = complex(derivative.subs(x, float(z) - eps)).real
                after_val = complex(derivative.subs(x, float(z) + eps)).real
            except (TypeError, ValueError):
                continue
            is_angular = z in piece_breakpoints
            if before_val > 0 and after_val < 0:
                kind = "maximum local"
            elif before_val < 0 and after_val > 0:
                kind = "minimum local"
            else:
                kind = "point anguleux (pas d'extremum)" if is_angular else "point stationnaire"
            if is_angular and kind in ("maximum local", "minimum local"):
                kind += " (point anguleux : dérivée non définie en ce point)"
            y0 = sp.simplify(expr.subs(x, z))
            points.append(CriticalPoint(x0=z, y0=y0, kind=kind, is_angular=is_angular))
    return points


def compute_inflection_points(expr: sp.Expr, second_derivative: sp.Expr, search_domain: sp.Set) -> List[InflectionPoint]:
    points = []
    for piece in _domain_pieces(search_domain):
        zeros = _safe_zeros_in(second_derivative, piece)
        for z in zeros:
            eps = 1e-3
            try:
                before_val = complex(second_derivative.subs(x, float(z) - eps)).real
                after_val = complex(second_derivative.subs(x, float(z) + eps)).real
            except (TypeError, ValueError):
                continue
            if (before_val > 0 and after_val < 0) or (before_val < 0 and after_val > 0):
                y0 = sp.simplify(expr.subs(x, z))
                points.append(InflectionPoint(x0=z, y0=y0))
    return points


def compute_limits_at_bounds(expr: sp.Expr, domain: sp.Set) -> List[Tuple[str, sp.Expr]]:
    """Calcule les limites aux bornes infinies du domaine (pas aux bornes finies :
    celles-ci sont couvertes par les asymptotes verticales, pour éviter les doublons)."""
    limits = []
    for piece in _domain_pieces(domain):
        if piece.start == -oo:
            try:
                lim = sp.limit(expr, x, -oo)
                limits.append(("-\\infty", lim if not isinstance(lim, sp.AccumBounds) else None))
            except Exception:
                pass
        if piece.end == oo:
            try:
                lim = sp.limit(expr, x, oo)
                limits.append(("+\\infty", lim if not isinstance(lim, sp.AccumBounds) else None))
            except Exception:
                pass
    # on retire les limites non déterminées (fonctions oscillantes type sin/cos en ±oo)
    return [(label, lim) for label, lim in limits if lim is not None]


def compute_asymptotes(expr: sp.Expr, domain: sp.Set) -> List[Asymptote]:
    asymptotes = []

    excluded = S.Reals - domain
    if isinstance(excluded, (FiniteSet, Union)):
        candidates = list(excluded) if isinstance(excluded, FiniteSet) else \
            [p for s in excluded.args if isinstance(s, FiniteSet) for p in s]
        for c in candidates:
            try:
                lim_left = sp.limit(expr, x, c, dir="-")
                lim_right = sp.limit(expr, x, c, dir="+")
                if lim_left in (oo, -oo) or lim_right in (oo, -oo):
                    asymptotes.append(Asymptote("verticale", f"x = {latex(c)}"))
            except Exception:
                continue

    for bound, label in [(oo, "+oo"), (-oo, "-oo")]:
        try:
            lim = sp.limit(expr, x, bound)
            if isinstance(lim, sp.AccumBounds):
                continue  # fonction oscillante : pas d'asymptote horizontale/oblique déterminable ainsi
            if lim.is_finite:
                asymptotes.append(Asymptote("horizontale", f"y = {latex(lim)} (en {label})"))
            else:
                a = sp.limit(expr / x, x, bound)
                if isinstance(a, sp.AccumBounds):
                    continue
                if a.is_finite and a != 0:
                    b = sp.limit(expr - a * x, x, bound)
                    if isinstance(b, sp.AccumBounds):
                        continue
                    if b.is_finite:
                        line_expr = sp.nsimplify(a) * x + sp.nsimplify(b)
                        asymptotes.append(Asymptote("oblique", f"y = {latex(line_expr)} (en {label})"))
        except Exception:
            continue

    return asymptotes


def analyze(expr_str: str) -> FunctionAnalysis:
    """Point d'entrée principal : analyse complète d'une fonction f(x)."""
    expr = parse_function(expr_str)
    domain = compute_domain(expr)
    parity = compute_parity(expr, domain)
    derivative = sp.simplify(sp.diff(expr, x))
    second_derivative = sp.simplify(sp.diff(derivative, x))

    study_domain, study_window_note = compute_study_domain(domain, expr)
    breakpoints = find_breakpoints(expr, study_domain)

    sign_intervals = compute_sign_intervals(derivative, study_domain, extra_breakpoints=breakpoints)
    critical_points = compute_critical_points(expr, derivative, study_domain)
    inflection_points = compute_inflection_points(expr, second_derivative, study_domain)
    asymptotes = compute_asymptotes(expr, domain)
    limits_at_bounds = compute_limits_at_bounds(expr, domain)

    return FunctionAnalysis(
        expr=expr,
        domain=domain,
        parity=parity,
        derivative=derivative,
        second_derivative=second_derivative,
        sign_intervals=sign_intervals,
        critical_points=critical_points,
        inflection_points=inflection_points,
        asymptotes=asymptotes,
        limits_at_bounds=limits_at_bounds,
        study_window_note=study_window_note,
    )
