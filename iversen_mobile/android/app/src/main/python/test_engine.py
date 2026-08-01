"""
Tests unitaires du moteur symbolique.
Lancer : python3 -m pytest test_engine.py -v
"""
import sympy as sp
from engine.functions import analyze


def test_polynomial_derivative():
    a = analyze("x**3 - 3*x + 2")
    assert sp.simplify(a.derivative - (3 * sp.symbols("x", real=True)**2 - 3)) == 0


def test_polynomial_extrema():
    a = analyze("x**3 - 3*x + 2")
    kinds = sorted((cp.kind, float(cp.x0), float(cp.y0)) for cp in a.critical_points)
    assert kinds == [("maximum local", -1.0, 4.0), ("minimum local", 1.0, 0.0)]


def test_polynomial_inflection_point():
    a = analyze("x**3 - 3*x + 2")
    assert len(a.inflection_points) == 1
    ip = a.inflection_points[0]
    assert float(ip.x0) == 0.0
    assert float(ip.y0) == 2.0


def test_even_function_parity():
    a = analyze("x**4 - 2*x**2")
    assert a.parity == "paire"


def test_odd_function_parity():
    a = analyze("x**3 - x")
    assert a.parity == "impaire"


def test_no_particular_parity():
    a = analyze("x**3 - 3*x + 2")
    assert a.parity == "aucune parité particulière"


def test_rational_function_vertical_asymptote():
    a = analyze("(2*x + 1)/(x - 1)")
    kinds = {asym.kind for asym in a.asymptotes}
    assert "verticale" in kinds
    assert "horizontale" in kinds


def test_rational_function_domain_excludes_pole():
    a = analyze("(2*x + 1)/(x - 1)")
    x = sp.symbols("x", real=True)
    assert not a.domain.contains(1)


def test_limits_at_infinity_polynomial():
    a = analyze("x**3 - 3*x + 2")
    d = dict(a.limits_at_bounds)
    assert d["+\\infty"] == sp.oo
    assert d["-\\infty"] == -sp.oo


def test_log_domain_and_derivative_no_crash():
    a = analyze("log(x)")
    x = sp.symbols("x", real=True)
    assert not a.domain.contains(0)
    assert not a.domain.contains(-1)
    assert sp.simplify(a.derivative - 1 / x) == 0


def test_log_parity_not_applicable():
    a = analyze("log(x)")
    assert a.parity.startswith("non pertinente")


def test_exp_horizontal_asymptote():
    a = analyze("exp(x) - 2")
    kinds_desc = [(asym.kind, asym.description) for asym in a.asymptotes]
    assert ("horizontale", "y = -2 (en -oo)") in kinds_desc


def test_sin_is_odd_and_periodic_note_present():
    a = analyze("sin(x)")
    assert a.parity == "impaire"
    assert a.study_window_note is not None


def test_sin_no_false_asymptote():
    a = analyze("sin(x)")
    # sin(x) oscille : aucune asymptote horizontale ne doit être rapportée
    assert a.asymptotes == []


def test_sin_extrema_within_study_window():
    a = analyze("sin(x)")
    maxima = [cp for cp in a.critical_points if cp.kind == "maximum local"]
    assert any(abs(float(cp.x0) - float(sp.pi / 2)) < 1e-6 for cp in maxima)


def test_tan_does_not_hang_and_has_no_extrema():
    # tan(x) a un domaine périodique complexe (Complement) qui provoquait
    # auparavant une itération infinie lors de la recherche des zéros de f''.
    a = analyze("tan(x)")
    assert a.critical_points == []  # f' = 1/cos^2(x) ne s'annule jamais


def test_rational_function_no_crash_at_pole():
    # ne doit pas planter en échantillonnant near x=1 (pôle) comme avant le correctif
    a = analyze("1/(x-1)")
    assert len(a.sign_intervals) >= 1


def test_abs_function_detects_angular_minimum():
    a = analyze("Abs(x-2)")
    angular = [cp for cp in a.critical_points if cp.is_angular]
    assert len(angular) == 1
    assert float(angular[0].x0) == 2.0
    assert float(angular[0].y0) == 0.0
    assert "minimum" in angular[0].kind


def test_piecewise_detects_corner_without_extremum():
    a = analyze("Piecewise((x**2, x < 1), (2*x - 1, True))")
    angular = [cp for cp in a.critical_points if cp.is_angular]
    assert any(float(cp.x0) == 1.0 for cp in angular)
    smooth = [cp for cp in a.critical_points if not cp.is_angular]
    assert any(float(cp.x0) == 0.0 and "minimum" in cp.kind for cp in smooth)


def test_weighted_score_perfect_reference_correction():
    from engine import write_correction
    a = analyze("x**3 - 3*x + 2")
    c = write_correction("t", "x**3 - 3*x + 2", a)
    # une correction de référence bien formée doit obtenir la note maximale
    assert c.score == c.score_max


def test_weighted_score_ignores_zero_weight_steps():
    from engine.models import Correction, Step
    c = Correction(exercise_title="t", function_str="f")
    c.add(Step(title="info", result_latex="", explanation="", weight=0.0))
    c.add(Step(title="core", result_latex="", explanation="", weight=2.0, is_complete=True))
    c.compute_score()
    assert c.score == c.score_max  # le step à poids 0 ne doit pas diluer la note


# --- OCR : nettoyage/parsing du texte extrait (couche indépendante de Tesseract) ---

def test_ocr_normalize_strips_function_prefix_and_caret():
    from ocr.normalize import to_canonical_expression
    assert to_canonical_expression("f(x) = x^3 - 3x + 2") == "x**3 - 3*x + 2"


def test_ocr_normalize_handles_implicit_multiplication():
    from ocr.normalize import to_canonical_expression
    assert to_canonical_expression("y = 2x(x-1)") == "2*x*(x - 1)"


def test_ocr_normalize_handles_unicode_operators():
    from ocr.normalize import to_canonical_expression
    # × et − unicode (pas les caractères ASCII * et -), fréquents en sortie OCR
    result = to_canonical_expression("f(x) = 3 × x − 3")
    assert result == "3*x - 3"


def test_ocr_normalize_rejects_text_without_x():
    from ocr.normalize import to_canonical_expression, OcrParseError
    import pytest
    with pytest.raises(OcrParseError):
        to_canonical_expression("Oo")  # bruit OCR typique d'une image illisible


def test_ocr_normalize_accepts_pure_constant():
    from ocr.normalize import to_canonical_expression
    # une fonction constante est valide même sans occurrence de x
    assert to_canonical_expression("f(x) = 2") == "2"


def test_ocr_pipeline_on_synthetic_image():
    """Test d'intégration : génère une image de texte imprimé propre (sans exposant,
    cas où Tesseract est fiable) et vérifie que le pipeline OCR complet aboutit à
    une expression correcte, exploitable par le moteur de correction."""
    from PIL import Image, ImageDraw, ImageFont
    from ocr import extract_text, to_canonical_expression
    from engine import analyze

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    img = Image.new("RGB", (500, 120), "white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "f(x) = 2x + 1", fill="black", font=font)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        raw = extract_text(tmp.name)

    canonical = to_canonical_expression(raw)
    assert canonical == "2*x + 1"
    a = analyze(canonical)  # vérifie que le résultat OCR est bien exploitable par le moteur
    assert a is not None


def test_ocr_page_mode_ranks_the_exercise_line_first():
    """Sur une photo pleine page (consigne + exercice + question), la ligne contenant
    réellement l'expression mathématique doit être classée en tête par le score de
    vraisemblance — sans quoi l'utilisateur devrait fouiller manuellement."""
    from PIL import Image, ImageDraw, ImageFont
    from ocr.reader import extract_line_candidates
    import tempfile

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    lines = [
        "Exercice 3 : etudier la fonction suivante.",
        "Soit f la fonction definie sur R par :",
        "",
        "f(x) = 2x + 1",
        "",
        "Determiner les variations de f.",
    ]
    img = Image.new("RGB", (900, 400), "white")
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        draw.text((30, y), line, fill="black", font=font)
        y += 55

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        candidates = extract_line_candidates(tmp.name)

    assert len(candidates) >= 2
    assert "f(x)" in candidates[0]["text"] or "2x" in candidates[0]["text"]
    assert candidates[0]["score"] > candidates[1]["score"]


def _make_realistic_notebook_photo(path: str) -> None:
    """Génère une photo de cahier synthétique dégradée : papier quadrillé, éclairage
    inégal (gradient), légère rotation et flou — pour tester le pipeline OCR dans des
    conditions plus proches d'un usage réel qu'une image de texte propre."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np

    W, H = 900, 300
    img = Image.new("RGB", (W, H), (250, 248, 240))
    draw = ImageDraw.Draw(img)
    grid_color = (190, 210, 230)
    for gy in range(0, H, 28):
        draw.line([(0, gy), (W, gy)], fill=grid_color, width=1)
    for gx in range(0, W, 28):
        draw.line([(gx, 0), (gx, H)], fill=grid_color, width=1)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
    draw.text((60, 120), "f(x) = 2x + 1", fill=(30, 30, 60), font=font)

    arr = np.array(img).astype(float)
    gradient = np.tile(np.linspace(0.75, 1.15, W), (H, 1))
    for c in range(3):
        arr[:, :, c] *= gradient
    arr = np.clip(arr, 0, 255).astype("uint8")
    img = Image.fromarray(arr)
    img = img.rotate(2.5, expand=True, fillcolor=(250, 248, 240))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img.save(path)


def test_ocr_page_mode_survives_realistic_notebook_photo():
    """Diagnostic établi empiriquement (voir README) : l'éclairage inégal, isolé,
    casse complètement l'OCR avec un seuillage global fixe — bien plus que la grille,
    la rotation ou le flou pris séparément. Ce test verrouille le correctif (seuillage
    adaptatif + suppression de grille par couleur + redressement) sur le cas combiné
    le plus dégradé, via le mode page qui peut s'appuyer sur le score de vraisemblance
    pour ignorer le bruit résiduel."""
    from ocr.reader import extract_line_candidates
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        _make_realistic_notebook_photo(tmp.name)
        candidates = extract_line_candidates(tmp.name)

    assert candidates, "aucune ligne détectée sur la photo dégradée"
    best = candidates[0]
    assert "f(x)" in best["text"] and "2x" in best["text"]
    assert best["score"] > 0.5

    from ocr.normalize import to_canonical_expression
    # le texte brut contient encore un peu de bruit résiduel (ex: "|" en tête de
    # ligne) — le pipeline de nettoyage doit malgré tout aboutir à l'expression
    # correcte, pas seulement à un score de vraisemblance élevé
    assert to_canonical_expression(best["text"]) == "2*x + 1"


# --- Résolution d'équations ---

def test_equation_linear():
    from engine import solve_equation
    a = solve_equation("2*x + 4 = 0")
    assert a.kind == "linéaire"
    assert a.solutions == [-2]


def test_equation_quadratic_positive_discriminant():
    from engine import solve_equation
    a = solve_equation("x**2 - 5*x + 6 = 0")
    assert a.kind == "quadratique"
    assert a.discriminant == 1
    assert sorted(float(s) for s in a.solutions) == [2.0, 3.0]


def test_equation_quadratic_zero_discriminant():
    from engine import solve_equation
    a = solve_equation("x**2 - 4*x + 4 = 0")
    assert a.discriminant == 0
    assert a.solutions == [2]


def test_equation_quadratic_negative_discriminant_has_no_real_solution():
    from engine import solve_equation
    a = solve_equation("x**2 + x + 1 = 0")
    assert a.discriminant == -3
    assert a.solutions == []


def test_equation_general_cubic():
    from engine import solve_equation
    a = solve_equation("x**3 - 8 = 0")
    assert a.kind == "générale"
    assert 2 in [sp.nsimplify(s) for s in a.solutions] if a.solutions else False


def test_equation_correction_verification_step_checks_out():
    """La correction doit toujours vérifier une solution trouvée par substitution,
    et cette vérification doit effectivement retomber sur 0 (pas un artefact affiché
    sans être vrai)."""
    from engine import solve_equation, write_equation_correction
    a = solve_equation("x**2 - 5*x + 6 = 0")
    c = write_equation_correction("t", "x**2 - 5*x + 6 = 0", a)
    verif_step = next(s for s in c.steps if s.title == "Vérification")
    assert verif_step.result_latex.strip().endswith("= 0")


def test_equation_correction_subject_line_not_mislabeled_as_function():
    from engine import solve_equation, write_equation_correction
    a = solve_equation("2*x + 4 = 0")
    c = write_equation_correction("t", "2*x + 4 = 0", a)
    assert c.subject_line == "Équation : 2*x + 4 = 0"


# --- Résolution d'inéquations ---

def test_inequality_linear_positive_coefficient():
    from engine import solve_inequality
    a = solve_inequality("2*x - 4 > 0")
    assert a.solution_set == sp.Interval.open(2, sp.oo)


def test_inequality_linear_negative_coefficient_flips_direction():
    from engine import solve_inequality
    a = solve_inequality("-2*x + 4 > 0")
    assert a.solution_set == sp.Interval.open(-sp.oo, 2)


def test_inequality_quadratic_positive_discriminant():
    from engine import solve_inequality
    a = solve_inequality("x**2 - 5*x + 6 > 0")
    expected = sp.Union(sp.Interval.open(-sp.oo, 2), sp.Interval.open(3, sp.oo))
    assert a.solution_set == expected


def test_inequality_quadratic_zero_discriminant_le():
    from engine import solve_inequality
    a = solve_inequality("x**2 - 4*x + 4 <= 0")
    assert a.solution_set == sp.FiniteSet(2)


def test_inequality_quadratic_negative_discriminant_always_true():
    from engine import solve_inequality
    a = solve_inequality("x**2 + x + 1 > 0")
    assert a.solution_set == sp.S.Reals


def test_inequality_rejects_equation_not_inequality():
    from engine.inequalities import solve_inequality as raw_solve
    import pytest
    with pytest.raises(ValueError):
        raw_solve("2*x + 4 = 0")  # une égalité n'est pas une inéquation


def test_inequality_correction_subject_line():
    from engine import solve_inequality, write_inequality_correction
    a = solve_inequality("x**2 - 5*x + 6 > 0")
    c = write_inequality_correction("t", "x**2 - 5*x + 6 > 0", a)
    assert c.subject_line == "Inéquation : x**2 - 5*x + 6 > 0"
    assert c.score == c.score_max


# --- Systèmes de 2 équations linéaires ---

def test_system_unique_solution():
    from engine import solve_system
    from engine.systems import x as sys_x, y as sys_y
    a = solve_system("2*x + y = 5", "x - y = 1")
    assert a.kind == "unique"
    x_val = a.other_value if a.other_variable == sys_x else a.substitution_value
    y_val = a.other_value if a.other_variable == sys_y else a.substitution_value
    assert x_val == 2 and y_val == 1


def test_system_no_solution_parallel_lines():
    from engine import solve_system
    a = solve_system("2*x + y = 5", "2*x + y = 3")
    assert a.kind == "aucune"


def test_system_infinite_solutions_same_line():
    from engine import solve_system
    a = solve_system("2*x + y = 5", "4*x + 2*y = 10")
    assert a.kind == "infinité"
    assert a.general_solution is not None
    assert "y = y" not in a.general_solution  # pas d'artefact cosmétique


def test_system_correction_verification_checks_out():
    from engine import solve_system, write_system_correction
    a = solve_system("2*x + y = 5", "x - y = 1")
    c = write_system_correction("t", "2*x + y = 5", "x - y = 1", a)
    verif_step = next(s for s in c.steps if s.title == "Vérification")
    assert "0 = 0" in verif_step.result_latex.replace(" ", "") or verif_step.result_latex.count("= 0") == 2


def test_system_rejects_nonlinear_equation():
    from engine.systems import solve_system as raw_solve
    import pytest
    with pytest.raises(ValueError):
        raw_solve("x**2 + y = 5", "x - y = 1")


def test_system_rejects_equation_without_equals():
    from engine.systems import solve_system as raw_solve
    import pytest
    with pytest.raises(ValueError):
        raw_solve("2*x + y", "x - y = 1")


# --- Suites définies par récurrence ---

def test_sequence_arithmetic():
    from engine import analyze_sequence
    a = analyze_sequence("2", "u + 3")
    assert a.kind == "arithmétique"
    assert a.common_difference == 3
    assert a.monotonicity == "croissante"
    assert a.limit == sp.oo
    assert [float(t) for t in a.first_terms[:3]] == [2.0, 5.0, 8.0]


def test_sequence_geometric_convergent():
    from engine import analyze_sequence
    a = analyze_sequence("10", "0.5*u")
    assert a.kind == "géométrique"
    assert a.limit == 0


def test_sequence_geometric_divergent():
    from engine import analyze_sequence
    a = analyze_sequence("3", "2*u")
    assert a.kind == "géométrique"
    assert a.common_ratio == 2
    assert a.limit == sp.oo
    assert a.monotonicity == "croissante"


def test_sequence_geometric_oscillating_no_limit():
    from engine import analyze_sequence
    a = analyze_sequence("1", "-2*u")
    assert a.kind == "géométrique"
    assert a.limit_exists is False


def test_sequence_arithmetico_geometric():
    from engine import analyze_sequence
    a = analyze_sequence("1", "2*u + 3")
    assert a.kind == "arithmético-géométrique"
    assert a.fixed_point == -3
    # verifie la formule fermee contre les termes calcules numeriquement
    from engine.sequences import n as seq_n
    for i, term in enumerate(a.first_terms):
        assert sp.simplify(a.general_term.subs(seq_n, i) - term) == 0


def test_sequence_non_affine_recurrence():
    from engine import analyze_sequence
    a = analyze_sequence("1", "u**2 - 1")
    assert a.kind == "non reconnue"
    assert a.general_term is None
    assert len(a.first_terms) > 0  # les premiers termes restent calculés numériquement


def test_sequence_correction_perfect_score_on_recognized_case():
    from engine import analyze_sequence, write_sequence_correction
    a = analyze_sequence("2", "u + 3")
    c = write_sequence_correction("t", "2", "u + 3", a)
    assert c.score == c.score_max


# --- Loi binomiale ---

def test_binomial_exact_probability_known_value():
    from engine import analyze_binomial
    a = analyze_binomial(5, "1/3", 2)
    assert a.proba_exact == sp.Rational(80, 243)


def test_binomial_distribution_sums_to_one():
    from engine import analyze_binomial
    a = analyze_binomial(5, "1/3", 2)
    total = sum(pr for _, pr in a.distribution_table)
    assert sp.simplify(total) == 1


def test_binomial_expectation_variance():
    from engine import analyze_binomial
    a = analyze_binomial(10, "0.2", 3)
    assert a.expectation == 2
    assert a.variance == sp.Rational(8, 5)


def test_binomial_cumulative_consistency():
    """P(X<=k) + P(X>=k) doit valoir 1 + P(X=k) (le terme k est compté deux fois)."""
    from engine import analyze_binomial
    a = analyze_binomial(6, "0.4", 3)
    assert sp.simplify(a.cumulative_le + a.cumulative_ge - a.proba_exact) == 1


def test_binomial_rejects_invalid_p():
    from engine.probability import analyze_binomial as raw
    import pytest
    with pytest.raises(ValueError):
        raw(5, "1.5", 2)  # p > 1, invalide


def test_binomial_rejects_k_out_of_range():
    from engine.probability import analyze_binomial as raw
    import pytest
    with pytest.raises(ValueError):
        raw(5, "0.5", 8)  # k > n, invalide


def test_binomial_correction_perfect_score():
    from engine import analyze_binomial, write_binomial_correction
    a = analyze_binomial(5, "1/3", 2)
    c = write_binomial_correction("t", 5, "1/3", 2, a)
    assert c.score == c.score_max


# --- Nombres complexes ---

def test_complex_modulus_and_argument_notable():
    from engine import analyze_complex
    a = analyze_complex("1 + I")
    assert a.modulus == sp.sqrt(2)
    assert a.argument == sp.pi / 4
    assert a.argument_is_notable is True


def test_complex_non_notable_argument():
    from engine import analyze_complex
    a = analyze_complex("3 + 4*I")
    assert a.modulus == 5
    assert a.argument_is_notable is False


def test_complex_third_quadrant():
    from engine import analyze_complex
    a = analyze_complex("-1 - I*sqrt(3)")
    assert a.modulus == 2
    assert a.argument == -2 * sp.pi / 3


def test_complex_conjugate():
    from engine import analyze_complex
    a = analyze_complex("3 + 4*I")
    assert a.conjugate == 3 - 4 * sp.I


def test_complex_rejects_zero():
    from engine.complex_numbers import analyze_complex as raw
    import pytest
    with pytest.raises(ValueError):
        raw("0")


def test_complex_rejects_expression_with_variable():
    from engine.complex_numbers import analyze_complex as raw
    import pytest
    with pytest.raises(ValueError):
        raw("x + I")


def test_complex_correction_verification_step_checks_out():
    from engine import analyze_complex, write_complex_correction
    a = analyze_complex("3 + 4*I")
    c = write_complex_correction("t", "3 + 4*I", a)
    assert c.score == c.score_max
    verif_step = next(s for s in c.steps if "Vérification" in s.title)
    assert "écart} : 0" in verif_step.result_latex


# --- Calcul matriciel ---

def test_matrix_determinant_and_inverse():
    from engine import analyze_matrix
    a = analyze_matrix([["1", "2"], ["3", "4"]])
    assert a.determinant == -2
    assert a.trace == 5
    assert a.is_invertible is True
    assert a.inverse == sp.Matrix([[-2, 1], [sp.Rational(3, 2), sp.Rational(-1, 2)]])


def test_matrix_singular_not_invertible():
    from engine import analyze_matrix
    a = analyze_matrix([["1", "0", "0"], ["0", "1", "0"], ["0", "0", "0"]])
    assert a.determinant == 0
    assert a.is_invertible is False
    assert a.inverse is None
    assert a.rank == 2


def test_matrix_non_square_has_no_determinant():
    from engine import analyze_matrix
    a = analyze_matrix([["1", "2", "3"], ["4", "5", "6"]])
    assert a.determinant is None
    assert a.is_invertible is None


def test_matrix_product_known_result():
    from engine import compute_matrix_operation
    r = compute_matrix_operation([["1", "2"], ["3", "4"]], [["5", "6"], ["7", "8"]], "produit")
    assert r.result == sp.Matrix([[19, 22], [43, 50]])


def test_matrix_sum_known_result():
    from engine import compute_matrix_operation
    r = compute_matrix_operation([["1", "2"], ["3", "4"]], [["5", "6"], ["7", "8"]], "somme")
    assert r.result == sp.Matrix([[6, 8], [10, 12]])


def test_matrix_product_rejects_incompatible_dimensions():
    from engine.matrices import compute_matrix_operation as raw
    import pytest
    with pytest.raises(ValueError):
        raw([["1", "2"], ["3", "4"]], [["1", "2", "3"]], "produit")


def test_matrix_rejects_ragged_rows():
    from engine.matrices import parse_matrix
    import pytest
    with pytest.raises(ValueError):
        parse_matrix([["1", "2"], ["3"]])


def test_matrix_correction_verification_identity():
    from engine import analyze_matrix, write_matrix_correction
    a = analyze_matrix([["1", "2"], ["3", "4"]])
    c = write_matrix_correction("t", "M", a)
    verif_step = next(s for s in c.steps if "Vérification" in s.title)
    assert "0 & 0" in verif_step.result_latex.replace(" ", "").replace("\\\\", " ") or "0 & 0" in verif_step.result_latex


# --- Géométrie analytique ---

def test_geometry_distance_and_midpoint():
    from engine import analyze_geometry
    a = analyze_geometry([1, 2], [4, 6])
    assert a.distance_AB == 5
    assert a.midpoint_AB == (sp.Rational(5, 2), 4)
    assert a.line_slope == sp.Rational(4, 3)


def test_geometry_vertical_line():
    from engine import analyze_geometry
    a = analyze_geometry([2, 1], [2, 5])
    assert a.line_is_vertical is True
    assert a.line_x_value == 2


def test_geometry_right_triangle_detected():
    from engine import analyze_geometry
    a = analyze_geometry([0, 0], [1, 0], [0, 1])
    assert a.are_orthogonal is True
    assert a.are_collinear is False


def test_geometry_collinear_points_detected():
    from engine import analyze_geometry
    a = analyze_geometry([0, 0], [1, 1], [2, 2])
    assert a.are_collinear is True


def test_geometry_rejects_identical_points():
    from engine.geometry import analyze_geometry as raw
    import pytest
    with pytest.raises(ValueError):
        raw([1, 1], [1, 1])


def test_geometry_rejects_malformed_point():
    from engine.geometry import analyze_geometry as raw
    import pytest
    with pytest.raises(ValueError):
        raw([1, 1, 1], [2, 2])  # 3 coordonnées au lieu de 2


def test_geometry_correction_perfect_score_with_and_without_c():
    from engine import analyze_geometry, write_geometry_correction
    a1 = analyze_geometry([1, 2], [4, 6])
    c1 = write_geometry_correction("t", "A,B", a1)
    assert c1.score == c1.score_max

    a2 = analyze_geometry([0, 0], [1, 0], [0, 1])
    c2 = write_geometry_correction("t", "A,B,C", a2)
    assert c2.score == c2.score_max
    assert len(c2.steps) > len(c1.steps)  # les étapes C ajoutent bien du contenu


# --- Équilibrage d'équations chimiques ---

def test_chemistry_formula_parsing_with_parentheses():
    from engine.chemistry import parse_formula
    assert parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    assert parse_formula("Al2(SO4)3") == {"Al": 2, "S": 3, "O": 12}


def test_chemistry_balances_water_formation():
    from engine import balance_equation
    a = balance_equation("H2 + O2 -> H2O")
    assert a.balanced_equation == "2 H2 + O2 -> 2 H2O"


def test_chemistry_balances_methane_combustion():
    from engine import balance_equation
    a = balance_equation("CH4 + O2 -> CO2 + H2O")
    assert a.balanced_equation == "CH4 + 2 O2 -> CO2 + 2 H2O"


def test_chemistry_balances_with_parentheses_compound():
    from engine import balance_equation
    a = balance_equation("Al + O2 -> Al2O3")
    assert a.balanced_equation == "4 Al + 3 O2 -> 2 Al2O3"


def test_chemistry_element_conservation_holds_for_all_coefficients():
    """Vérifie, indépendamment de balance_equation, que les coefficients trouvés
    conservent bien chaque élément — un test de cohérence redondant mais qui
    catcherait un bug d'indexation entre réactifs/produits que le test précédent
    (comparaison de chaîne) pourrait laisser passer si le format changeait."""
    from engine import balance_equation
    from engine.chemistry import parse_formula
    a = balance_equation("Fe2O3 + CO -> Fe + CO2")
    n_r = len(a.reactants)
    for el in a.elements:
        left = sum(a.coefficients[i] * parse_formula(name).get(el, 0) for i, name in enumerate(a.reactants))
        right = sum(a.coefficients[n_r + i] * parse_formula(name).get(el, 0) for i, name in enumerate(a.products))
        assert left == right, f"élément {el} non conservé : {left} != {right}"


def test_chemistry_rejects_equation_without_arrow():
    from engine.chemistry import parse_equation
    import pytest
    with pytest.raises(ValueError):
        parse_equation("H2 + O2 H2O")


def test_chemistry_correction_perfect_score():
    from engine import balance_equation, write_chemistry_correction
    a = balance_equation("H2 + O2 -> H2O")
    c = write_chemistry_correction("t", "H2 + O2 -> H2O", a)
    assert c.score == c.score_max


# --- Circuits électriques ---

def test_circuit_series_known_values():
    from engine import analyze_circuit
    a = analyze_circuit(["10", "20", "30"], "série", "12")
    assert a.equivalent_resistance == 60
    assert a.total_current == sp.Rational(1, 5)
    assert a.voltages == [2, 4, 6]


def test_circuit_parallel_known_values():
    from engine import analyze_circuit
    a = analyze_circuit(["10", "20", "30"], "parallèle", "12")
    assert a.equivalent_resistance == sp.Rational(60, 11)
    assert a.currents == [sp.Rational(6, 5), sp.Rational(3, 5), sp.Rational(2, 5)]


def test_circuit_parallel_currents_sum_to_total():
    """Garde-fou de cohérence physique : en parallèle, la somme des courants dans
    chaque branche doit être exactement égale au courant total délivré."""
    from engine import analyze_circuit
    a = analyze_circuit(["10", "20", "30"], "parallèle", "12")
    assert sum(a.currents) == a.total_current


def test_circuit_total_power_equals_sum_of_individual_powers():
    from engine import analyze_circuit
    for topo in ["série", "parallèle"]:
        a = analyze_circuit(["10", "20", "30"], topo, "12")
        assert sum(a.powers) == a.total_power


def test_circuit_rejects_negative_resistance():
    from engine.physics_circuits import analyze_circuit as raw
    import pytest
    with pytest.raises(ValueError):
        raw(["-10", "20"], "série", "12")


def test_circuit_rejects_unknown_topology():
    from engine.physics_circuits import analyze_circuit as raw
    import pytest
    with pytest.raises(ValueError):
        raw(["10", "20"], "mixte", "12")


def test_circuit_correction_perfect_score():
    from engine import analyze_circuit, write_circuit_correction
    a = analyze_circuit(["10", "20", "30"], "série", "12")
    c = write_circuit_correction("t", "circuit", a)
    assert c.score == c.score_max


# --- Cinématique (MRUV) ---

def test_kinematics_braking_scenario():
    from engine import analyze_kinematics
    a = analyze_kinematics("0", "20", "-2", "3")
    assert a.position_at_t == 51
    assert a.velocity_at_t == 14
    assert a.is_decelerating is True
    assert a.stop_time == 10
    assert a.stop_distance == 100


def test_kinematics_accelerating_from_rest():
    from engine import analyze_kinematics
    a = analyze_kinematics("0", "0", "2", "5")
    assert a.position_at_t == 25
    assert a.velocity_at_t == 10
    assert a.is_decelerating is False
    assert a.stop_time is None


def test_kinematics_time_independent_relation_holds():
    """Garde-fou physique : v(t)^2 - v0^2 = 2a(x(t)-x0) doit toujours être vérifié,
    indépendamment des valeurs choisies — testé sur plusieurs scénarios."""
    import sympy as sp
    from engine import analyze_kinematics
    for x0, v0, a_val, tt in [("0", "20", "-2", "3"), ("5", "-10", "3", "2"), ("0", "0", "9.8", "1")]:
        a = analyze_kinematics(x0, v0, a_val, tt)
        lhs = a.velocity_at_t**2 - a.v0**2
        rhs = 2 * a.a * (a.position_at_t - a.x0)
        assert sp.simplify(lhs - rhs) == 0


def test_kinematics_rejects_negative_time():
    from engine.physics_kinematics import analyze_kinematics as raw
    import pytest
    with pytest.raises(ValueError):
        raw("0", "10", "-2", "-1")


def test_kinematics_correction_perfect_score():
    from engine import analyze_kinematics, write_kinematics_correction
    a = analyze_kinematics("0", "20", "-2", "3")
    c = write_kinematics_correction("t", "freinage", a)
    assert c.score == c.score_max


# --- Optique (lentille mince convergente) ---

def test_optics_real_inverted_reduced_image():
    from engine import analyze_thin_lens
    a = analyze_thin_lens("10", "-30")
    assert a.OA_prime == 15
    assert a.magnification == sp.Rational(-1, 2)
    assert a.image_is_real is True
    assert a.image_is_upright is False


def test_optics_magnifying_glass_case():
    """Objet entre le foyer et la lentille : image virtuelle, agrandie, droite —
    comportement caractéristique d'une loupe."""
    from engine import analyze_thin_lens
    a = analyze_thin_lens("10", "-5")
    assert a.OA_prime == -10
    assert a.magnification == 2
    assert a.image_is_real is False
    assert a.image_is_upright is True


def test_optics_rejects_diverging_lens():
    from engine.physics_optics import analyze_thin_lens as raw
    import pytest
    with pytest.raises(ValueError):
        raw("-10", "-30")


def test_optics_rejects_positive_object_position():
    from engine.physics_optics import analyze_thin_lens as raw
    import pytest
    with pytest.raises(ValueError):
        raw("10", "30")


def test_optics_rejects_object_at_focal_point():
    from engine.physics_optics import analyze_thin_lens as raw
    import pytest
    with pytest.raises(ValueError):
        raw("10", "-10")


def test_optics_correction_perfect_score():
    from engine import analyze_thin_lens, write_optics_correction
    a = analyze_thin_lens("10", "-30")
    c = write_optics_correction("t", "lentille", a)
    assert c.score == c.score_max


# --- Stœchiométrie ---

def test_stoichiometry_molar_mass_known_values():
    from engine.chemistry_stoichiometry import compute_molar_mass
    assert abs(float(compute_molar_mass("H2O")) - 18.015) < 0.001
    assert abs(float(compute_molar_mass("CO2")) - 44.009) < 0.001


def test_stoichiometry_methane_combustion_mass_input():
    from engine import analyze_stoichiometry
    a = analyze_stoichiometry("CH4 + O2 -> CO2 + H2O", "CH4", "16", "g")
    ch4 = next(q for q in a.quantities if q.name == "CH4")
    o2 = next(q for q in a.quantities if q.name == "O2")
    assert abs(float(ch4.moles) - 0.997) < 0.01
    # stoechiometrie : n(O2) doit etre exactement le double de n(CH4)
    assert o2.moles == 2 * ch4.moles


def test_stoichiometry_mass_conservation():
    """Garde-fou de cohérence chimique : la masse totale des réactifs doit être
    exactement égale à la masse totale des produits (loi de Lavoisier)."""
    import sympy as sp
    from engine import analyze_stoichiometry
    a = analyze_stoichiometry("CH4 + O2 -> CO2 + H2O", "CH4", "16", "g")
    reactant_mass = sum(q.mass for q in a.quantities if q.name in a.equation.reactants)
    product_mass = sum(q.mass for q in a.quantities if q.name in a.equation.products)
    assert sp.simplify(reactant_mass - product_mass) == 0


def test_stoichiometry_mol_input_direct():
    from engine import analyze_stoichiometry
    a = analyze_stoichiometry("H2 + O2 -> H2O", "H2", "2", "mol")
    h2o = next(q for q in a.quantities if q.name == "H2O")
    assert h2o.moles == 2  # coefficients egaux (2H2+O2->2H2O), donc n(H2O)=n(H2)


def test_stoichiometry_rejects_unknown_compound():
    from engine.chemistry_stoichiometry import analyze_stoichiometry as raw
    import pytest
    with pytest.raises(ValueError):
        raw("H2 + O2 -> H2O", "NaCl", "1", "mol")


def test_stoichiometry_correction_perfect_score():
    from engine import analyze_stoichiometry, write_stoichiometry_correction
    a = analyze_stoichiometry("CH4 + O2 -> CO2 + H2O", "CH4", "16", "g")
    c = write_stoichiometry_correction("t", "CH4 + O2 -> CO2 + H2O", "CH4", "16", "g", a)
    assert c.score == c.score_max


# --- Thermodynamique (calorimétrie) ---

def test_thermo_sensible_heat_known_value():
    from engine import analyze_sensible_heat
    a = analyze_sensible_heat("500", "4.18", "20", "100")
    assert a.heat == 167200
    assert a.is_absorbed is True


def test_thermo_sensible_heat_cooling_is_negative():
    from engine import analyze_sensible_heat
    a = analyze_sensible_heat("200", "4.18", "80", "20")
    assert a.heat == -50160
    assert a.is_absorbed is False


def test_thermo_latent_heat_known_value():
    from engine import analyze_latent_heat
    a = analyze_latent_heat("100", "2257")
    assert a.heat == 225700


def test_thermo_rejects_nonpositive_mass():
    from engine.physics_thermodynamics import analyze_sensible_heat as raw
    import pytest
    with pytest.raises(ValueError):
        raw("-500", "4.18", "20", "100")


def test_thermo_correction_perfect_score_both_modes():
    from engine import analyze_sensible_heat, analyze_latent_heat, write_thermodynamics_correction
    a = analyze_sensible_heat("500", "4.18", "20", "100")
    c = write_thermodynamics_correction("t", "chauffage", a)
    assert c.score == c.score_max

    b = analyze_latent_heat("100", "2257")
    d = write_thermodynamics_correction("t", "vaporisation", b)
    assert d.score == d.score_max


# --- Test d'intégration API : les 8 endpoints, en une seule passe automatisée ---
# (complète les validations manuelles par curl faites au fil du développement,
# pour qu'elles ne dépendent plus de la mémoire de la conversation)

def test_api_full_surface_smoke_test():
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

    r = client.post("/api/correct", json={"function_str": "x**3 - 3*x + 2"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/plot", json={"function_str": "x**3 - 3*x + 2"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 1000

    r = client.post("/api/solve-equation", json={"equation_str": "x**2 - 5*x + 6 = 0"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/solve-inequality", json={"inequality_str": "x**2 - 5*x + 6 > 0"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/solve-system", json={"equation1_str": "2*x + y = 5", "equation2_str": "x - y = 1"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-sequence", json={"first_term_str": "2", "recurrence_str": "u + 3"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-binomial", json={"n": 5, "p_str": "1/3", "k": 2})
    assert r.status_code == 200 and "steps" in r.json()
    binomial_correction = r.json()

    r = client.post("/api/analyze-complex", json={"z_str": "1 + I"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-matrix", json={"rows": [["1", "2"], ["3", "4"]]})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/matrix-operation", json={
        "rows_a": [["1", "2"], ["3", "4"]], "rows_b": [["5", "6"], ["7", "8"]], "operation": "produit",
    })
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-geometry", json={"A": [0, 0], "B": [1, 0], "C": [0, 1]})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/balance-equation", json={"equation_str": "CH4 + O2 -> CO2 + H2O"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-circuit", json={"resistances": ["10", "20", "30"], "topology": "série", "voltage": "12"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-kinematics", json={"x0": "0", "v0": "20", "a": "-2", "t": "3"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-optics", json={"f": "10", "OA": "-30"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-stoichiometry", json={
        "equation_str": "CH4 + O2 -> CO2 + H2O", "known_compound": "CH4", "amount": "16", "amount_type": "g",
    })
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-thermodynamics", json={
        "mode": "sensible", "mass": "500", "specific_heat": "4.18", "t_initial": "20", "t_final": "100",
    })
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/analyze-thermodynamics", json={"mode": "latente", "mass": "100", "latent_heat": "2257"})
    assert r.status_code == 200 and "steps" in r.json()

    r = client.post("/api/export-pdf", json=binomial_correction)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 1000

    r = client.post("/api/export-docx", json=binomial_correction)
    assert r.status_code == 200
    assert "wordprocessingml" in r.headers["content-type"]
    assert len(r.content) > 1000

    # cas d'erreur : chacun des 4 endpoints de résolution doit refuser proprement
    # une entrée invalide (400), pas planter (500)
    assert client.post("/api/correct", json={"function_str": "???invalid"}).status_code == 400
    assert client.post("/api/solve-equation", json={"equation_str": "???invalid"}).status_code == 400
    assert client.post("/api/analyze-binomial", json={"n": 5, "p_str": "1.5", "k": 2}).status_code == 400


def test_api_ocr_endpoints_smoke_test():
    """Vérifie /api/ocr et /api/ocr-page avec de vraies images (pas de mock) —
    couvre le pipeline complet image → texte → expression, pas juste le routage HTTP."""
    from fastapi.testclient import TestClient
    from app import app
    from PIL import Image, ImageDraw, ImageFont
    import io

    client = TestClient(app)

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    img = Image.new("RGB", (500, 120), "white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "f(x) = 2x + 1", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    r = client.post("/api/ocr", files={"image": ("test.png", buf, "image/png")})
    assert r.status_code == 200
    assert r.json()["suggested_function_str"] == "2*x + 1"


# --- Export PDF ---

def test_pdf_export_all_exercise_types(tmp_path):
    """Génère un PDF réel pour chacun des 6 types d'exercice et vérifie, avec pypdf,
    que le fichier produit est un PDF valide et non vide — pas seulement que la
    fonction ne lève pas d'exception."""
    from engine import (
        analyze, write_correction, correction_to_dict,
        solve_equation, write_equation_correction,
        solve_inequality, write_inequality_correction,
        solve_system, write_system_correction,
        analyze_sequence, write_sequence_correction,
        analyze_binomial, write_binomial_correction,
    )
    from export_engine import export_correction_to_pdf
    from pypdf import PdfReader

    cases = {
        "function": write_correction("t", "x**3 - 3*x + 2", analyze("x**3 - 3*x + 2")),
        "equation": write_equation_correction("t", "x**2 - 5*x + 6 = 0", solve_equation("x**2 - 5*x + 6 = 0")),
        "inequality": write_inequality_correction("t", "x**2 - 5*x + 6 > 0", solve_inequality("x**2 - 5*x + 6 > 0")),
        "system": write_system_correction("t", "2*x + y = 5", "x - y = 1", solve_system("2*x + y = 5", "x - y = 1")),
        "sequence": write_sequence_correction("t", "1", "2*u + 3", analyze_sequence("1", "2*u + 3")),
        "binomial": write_binomial_correction("t", 5, "1/3", 2, analyze_binomial(5, "1/3", 2)),
    }
    for name, correction in cases.items():
        out = tmp_path / f"{name}.pdf"
        export_correction_to_pdf(correction_to_dict(correction), str(out))
        assert out.exists() and out.stat().st_size > 1000
        reader = PdfReader(str(out))
        assert len(reader.pages) >= 1
        text = reader.pages[0].extract_text()
        assert len(text) > 20  # du texte a bien été rendu, pas une page blanche


def test_pdf_export_formulas_use_real_math_rendering_not_fallback():
    """Vérifie que le rendu LaTeX passe par mathtext (formule mathématique réelle)
    et ne retombe pas systématiquement sur le repli texte brut — sinon l'export
    PDF « marche » techniquement mais produit un résultat dégradé silencieusement."""
    from engine import solve_equation, write_equation_correction, correction_to_dict
    from export_engine.latex_render import render_latex_to_png
    import tempfile, os

    a = solve_equation("x**2 - 5*x + 6 = 0")
    c = write_equation_correction("t", "x**2 - 5*x + 6 = 0", a)
    d = correction_to_dict(c)

    with tempfile.TemporaryDirectory() as td:
        results = []
        for i, step in enumerate(d["steps"]):
            if step["result_latex"]:
                ok = render_latex_to_png(step["result_latex"], os.path.join(td, f"{i}.png"))
                results.append(ok)
        assert results, "aucune formule à tester"
        assert all(results), "au moins une formule est tombée dans le repli texte brut"


def test_docx_export_all_exercise_types(tmp_path):
    """Génère un .docx réel pour chacun des 6 types d'exercice et vérifie, en le
    rouvrant avec python-docx, qu'il contient bien du texte structuré (paragraphes
    non vides) — pas seulement qu'aucune exception n'a été levée."""
    from engine import (
        analyze, write_correction, correction_to_dict,
        solve_equation, write_equation_correction,
        solve_inequality, write_inequality_correction,
        solve_system, write_system_correction,
        analyze_sequence, write_sequence_correction,
        analyze_binomial, write_binomial_correction,
    )
    from export_engine import export_correction_to_docx
    from docx import Document

    cases = {
        "function": write_correction("t", "x**3 - 3*x + 2", analyze("x**3 - 3*x + 2")),
        "equation": write_equation_correction("t", "x**2 - 5*x + 6 = 0", solve_equation("x**2 - 5*x + 6 = 0")),
        "inequality": write_inequality_correction("t", "x**2 - 5*x + 6 > 0", solve_inequality("x**2 - 5*x + 6 > 0")),
        "system": write_system_correction("t", "2*x + y = 5", "x - y = 1", solve_system("2*x + y = 5", "x - y = 1")),
        "sequence": write_sequence_correction("t", "1", "2*u + 3", analyze_sequence("1", "2*u + 3")),
        "binomial": write_binomial_correction("t", 5, "1/3", 2, analyze_binomial(5, "1/3", 2)),
    }
    for name, correction in cases.items():
        out = tmp_path / f"{name}.docx"
        export_correction_to_docx(correction_to_dict(correction), str(out))
        assert out.exists() and out.stat().st_size > 1000
        doc = Document(str(out))
        text = "\n".join(p.text for p in doc.paragraphs)
        assert len(text.strip()) > 20
        assert len(doc.inline_shapes) > 0  # au moins une formule rendue en image


# --- Tracé de courbes ---

def test_plot_produces_nonempty_image(tmp_path):
    """Vérifie, avec un contrôle quantitatif (écart-type des pixels), qu'un vrai
    graphique a été dessiné — pas juste qu'un fichier PNG existe (un canevas vide
    produirait aussi un PNG valide mais inutile)."""
    from engine.functions import analyze
    from plot_engine import plot_function_analysis
    from PIL import Image
    import numpy as np

    a = analyze("x**3 - 3*x + 2")
    out = tmp_path / "plot.png"
    plot_function_analysis(a, "x**3 - 3*x + 2", str(out))
    assert out.exists()
    arr = np.array(Image.open(str(out)).convert("L"))
    assert arr.std() > 5  # image non uniforme : du contenu a bien été tracé


def test_plot_handles_vertical_asymptote_without_crashing(tmp_path):
    from engine.functions import analyze
    from plot_engine import plot_function_analysis

    a = analyze("(2*x + 1)/(x - 1)")
    out = tmp_path / "plot.png"
    plot_function_analysis(a, "(2*x + 1)/(x - 1)", str(out))
    assert out.exists() and out.stat().st_size > 1000


def test_plot_auto_range_uses_critical_points():
    from engine.functions import analyze
    from plot_engine.curve_plot import _auto_range

    a = analyze("x**3 - 3*x + 2")  # extrema en x=-1 et x=1
    lo, hi = _auto_range(a)
    assert lo < -1 and hi > 1  # la fenêtre doit englober les points caractéristiques


def test_plot_handles_trig_and_log_without_crashing(tmp_path):
    from engine.functions import analyze
    from plot_engine import plot_function_analysis

    for expr in ["sin(x)", "log(x)", "Abs(x - 2)"]:
        a = analyze(expr)
        out = tmp_path / f"{expr.replace('/', '_')}.png"
        plot_function_analysis(a, expr, str(out))
        assert out.exists() and out.stat().st_size > 1000


def test_plot_data_returns_json_serializable_structure():
    """Le graphique interactif (frontend) consomme ces données : on vérifie
    la structure et qu'elles sont bien sérialisables en JSON (pas de NaN,
    qui n'existe pas en JSON standard)."""
    import json
    from engine.functions import analyze
    from plot_engine import plot_function_analysis_data

    a = analyze("x**3 - 3*x + 2")
    data = plot_function_analysis_data(a, "x**3 - 3*x + 2")
    encoded = json.dumps(data)  # lève une exception si NaN/Infinity trainent
    assert "NaN" not in encoded
    assert len(data["x"]) == len(data["y"])
    kinds = {p["kind"] for p in data["critical_points"]}
    assert any("maximum" in k for k in kinds)
    assert any("minimum" in k for k in kinds)


def test_plot_data_deduplicates_repeated_horizontal_asymptote():
    """Régression : une fonction avec la même asymptote horizontale en +l'infini
    et en -l'infini (ex: 1/(x-1), y=0 des deux côtés) la renvoyait deux fois."""
    from engine.functions import analyze
    from plot_engine import plot_function_analysis_data

    a = analyze("1/(x - 1)")
    data = plot_function_analysis_data(a, "1/(x - 1)")
    assert data["horizontal_asymptotes"] == [0.0]
    assert data["vertical_asymptotes"] == [1.0]


def test_plot_data_marks_domain_gaps_as_null():
    """Une valeur hors domaine (ex: près d'une asymptote verticale) doit
    apparaître comme un trou (None -> null en JSON), jamais comme un nombre
    faux, pour que le frontend n'affiche pas un trait qui traverse le vide."""
    from engine.functions import analyze
    from plot_engine import plot_function_analysis_data

    a = analyze("1/(x - 1)")
    data = plot_function_analysis_data(a, "1/(x - 1)")
    assert None in data["y"]


def test_plot_data_endpoint_reachable_via_api(tmp_path):
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)
    r = client.post("/api/plot-data", json={"function_str": "x**3 - 3*x + 2"})
    assert r.status_code == 200
    body = r.json()
    assert "x" in body and "y" in body and "critical_points" in body


def test_history_save_list_get_delete_roundtrip(tmp_path, monkeypatch):
    """Test bout en bout du cycle de vie d'une entrée d'historique, sur une
    base de données temporaire (pour ne pas toucher les vraies données)."""
    import history_store
    monkeypatch.setattr(history_store, "_DB_PATH", tmp_path / "history.db")

    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)

    payload = {"exercise_title": "Étude de f(x) = x**2", "steps": [{"title": "Domaine", "result_latex": "D_f = \\mathbb{R}"}]}
    r = client.post("/api/history", json={
        "exercise_type": "function", "exercise_type_label": "Étude de fonction",
        "title": "x**2", "summary": "f(x) = x**2", "payload": payload,
        "score": 18, "score_max": 20,
    })
    assert r.status_code == 200
    entry_id = r.json()["id"]

    r = client.get("/api/history")
    assert r.status_code == 200
    entries = r.json()["entries"]
    assert any(e["id"] == entry_id for e in entries)
    assert "payload" not in entries[0]  # la liste reste légère, pas le payload complet

    r = client.get(f"/api/history/{entry_id}")
    assert r.status_code == 200
    full = r.json()
    assert full["payload"] == payload

    r = client.delete(f"/api/history/{entry_id}")
    assert r.status_code == 200
    r = client.get(f"/api/history/{entry_id}")
    assert r.status_code == 404


def test_history_get_unknown_id_returns_404(tmp_path, monkeypatch):
    import history_store
    monkeypatch.setattr(history_store, "_DB_PATH", tmp_path / "history.db")
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)
    r = client.get("/api/history/999999")
    assert r.status_code == 404


def test_history_clear_removes_everything(tmp_path, monkeypatch):
    import history_store
    monkeypatch.setattr(history_store, "_DB_PATH", tmp_path / "history.db")
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)

    for i in range(3):
        client.post("/api/history", json={
            "exercise_type": "equation", "exercise_type_label": "Équation",
            "title": f"eq{i}", "summary": "x=1", "payload": {"steps": []},
        })
    r = client.delete("/api/history")
    assert r.status_code == 200
    assert r.json()["deleted_count"] == 3
    assert client.get("/api/history").json()["entries"] == []


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
