"""
API — expose le moteur de correction (engine/) sur HTTP, pour l'appeler depuis
n'importe quel client (web ici, Flutter plus tard : même contrat d'API).

Lancer :
    pip install -r requirements.txt
    uvicorn app:app --reload --port 8000

Puis ouvrir frontend/index.html dans un navigateur (il appelle localhost:8000).
"""
import concurrent.futures
import multiprocessing as mp
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import (
    analyze, write_correction, correction_to_dict,
    solve_equation, write_equation_correction,
    solve_inequality, write_inequality_correction,
    solve_system, write_system_correction,
    analyze_sequence, write_sequence_correction,
    analyze_binomial, write_binomial_correction,
    analyze_complex, write_complex_correction,
    analyze_matrix, compute_matrix_operation,
    write_matrix_correction, write_matrix_operation_correction,
    analyze_geometry, write_geometry_correction,
    balance_equation, write_chemistry_correction,
    analyze_circuit, write_circuit_correction,
    analyze_kinematics, write_kinematics_correction,
    analyze_thin_lens, write_optics_correction,
    analyze_stoichiometry, write_stoichiometry_correction,
    analyze_sensible_heat, analyze_latent_heat, write_thermodynamics_correction,
    analyze_integral, write_integral_correction,
)
from ocr import extract_text, clean_text, to_canonical_expression, OcrParseError, OcrUnavailableError, OCR_AVAILABLE
from ocr.reader import extract_line_candidates
from export_engine import export_correction_to_pdf, export_correction_to_docx
from plot_engine import plot_function_analysis_bytes, plot_function_analysis_data
import history_store

_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def to_display(expr_str: str) -> str:
    """Convertit une expression en notation Python ('x**3 - 3*x + 2') en une
    version lisible pour l'affichage seulement ('x³ - 3x + 2') : exposants en
    caractères Unicode, multiplication implicite. Ne touche jamais au champ
    original envoyé au moteur (function_str, etc.), qui reste inchangé et
    reste donc toujours calculable."""
    import re
    def _exp_repl(m):
        return m.group(1) + m.group(2).translate(_SUPERSCRIPTS)
    s = re.sub(r"([A-Za-z0-9\)])\*\*(\d+)", _exp_repl, expr_str)
    s = re.sub(r"(\d)\*([A-Za-z\(])", r"\1\2", s)
    s = s.replace("*", "×")
    return s


app = FastAPI(title="Iversen Scientific — Moteur de correction (Phase 1 + OCR)")

# CORS : le frontend web ET la version bureau sont servis en same-origin par
# cette même API FastAPI (voir frontend/index.html : `const API = ""`, et
# run_desktop.py qui ouvre http://127.0.0.1:8000) — CORS n'est donc pas requis
# pour l'usage normal (le navigateur n'applique pas cette restriction pour des
# requêtes same-origin). L'app mobile Flutter n'est pas non plus concernée : un
# client HTTP natif n'envoie pas d'en-tête Origin, CORS ne s'y applique pas.
#
# `allow_origins=["*"]` restait donc une ouverture inutile — et concrètement
# dangereuse une fois l'app installée en local : n'importe quel site visité
# dans le navigateur de l'utilisateur pouvait, pendant que le serveur local
# tourne, interroger http://127.0.0.1:8000/api/... en arrière-plan (ex: lire
# tout l'historique d'exercices) puisque le serveur répondait "oui" à
# n'importe quelle origine. On restreint donc par défaut aux origines locales
# légitimes, avec une échappatoire par variable d'environnement pour un
# déploiement hébergé avec un frontend sur un domaine séparé.
_default_cors_origins = [
    "http://127.0.0.1:8000", "http://localhost:8000",
    "http://127.0.0.1:5173", "http://localhost:5173",  # ports de dev usuels
]
_env_cors_origins = os.environ.get("IVERSEN_CORS_ORIGINS", "").strip()
_cors_origins = (
    [o.strip() for o in _env_cors_origins.split(",") if o.strip()]
    if _env_cors_origins else _default_cors_origins
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Le moteur symbolique est déterministe mais certaines entrées transcendantes
# pathologiques pourraient en théorie rendre un sous-calcul SymPy très lent.
# On borne chaque requête dans le temps par défense en profondeur, en plus des
# garde-fous déjà en place dans engine/functions.py (voir _domain_pieces).
REQUEST_TIMEOUT_SECONDS = 10

# IMPORTANT — pourquoi un processus dédié par requête, et pas un ThreadPoolExecutor :
#
# La version précédente soumettait chaque calcul à un ThreadPoolExecutor partagé
# (4 workers) et abandonnait juste l'attente avec future.result(timeout=...) en
# cas de dépassement. Mais annuler l'ATTENTE ne stoppe pas le THREAD : un calcul
# SymPy resté bloqué (équation pathologique, racines symboliques très lourdes...)
# continuait de tourner indéfiniment en arrière-plan, en tenant occupé un des 4
# emplacements du pool pour de bon. À l'usage, ces threads « zombies »
# s'accumulaient et finissaient par épuiser tout le pool — si bien que des
# requêtes ensuite parfaitement anodines et rapides (ex: tracer la courbe de
# (x³-1)/(x+2), qui se calcule en réalité en moins d'une seconde) se
# retrouvaient à attendre un emplacement libre... et expiraient elles aussi,
# avec le même message trompeur « trop complexe ». De plus, le GIL de Python
# fait qu'un calcul SymPy (pur Python, CPU-bound) dans un thread peut ralentir
# tous les autres threads du même processus pendant qu'il tourne.
#
# On isole donc chaque requête dans son propre processus système : si elle
# dépasse le délai, on la termine réellement (terminate/kill), ce qui libère
# la mémoire ET le CPU immédiatement, sans jamais pouvoir affamer les requêtes
# suivantes. C'est aussi une isolation plus sûre : un crash bas niveau d'une
# dépendance (matplotlib, tesseract...) sur une entrée pathologique ne peut
# pas faire tomber tout le serveur, juste ce process-là.
#
# "forkserver" plutôt que "fork" : uvicorn/Starlette exécutent les endpoints
# synchrones dans un pool de threads. Appeler fork() depuis un processus déjà
# multi-thread est une source connue de deadlocks (un verrou détenu par un
# autre thread au moment du fork reste bloqué pour toujours dans l'enfant, qui
# n'a hérité que du thread appelant). "forkserver" évite ce piège : un
# processus auxiliaire dédié, lancé au démarrage AVANT que d'autres threads
# n'existent, se charge de dupliquer les workers à la demande. C'est pour ça
# que chaque tâche est désormais une fonction nommée au niveau du module
# (ci-dessous, _task_*) plutôt qu'une closure : forkserver (comme spawn, son
# repli sur Windows) a besoin de pouvoir sérialiser la cible par référence.
_MP_START_METHOD = (
    "forkserver" if "forkserver" in mp.get_all_start_methods()
    else "spawn" if "spawn" in mp.get_all_start_methods()
    else None
)
# Cas particulier : ce même fichier tourne aussi embarqué sur Android via
# Chaquopy (voir iversen_mobile/android/app/src/main/python/), où le moteur
# Python est intégré dans le processus applicatif unique de l'app — il n'y a
# ni fork() ni possibilité de lancer un second interpréteur Python (sandbox
# Android). `multiprocessing` peut y sembler disponible côté API sans
# fonctionner réellement à l'exécution (blocage silencieux, crash natif...).
# On désactive donc explicitement l'isolation par processus sur Android et on
# se rabat sur le mode thread ci-dessous — moins strict sur les blocages,
# mais sans risque de casser l'app, et acceptable ici car un téléphone n'a
# qu'un seul utilisateur à la fois (pas de scénario d'épuisement d'un pool
# partagé entre plusieurs utilisateurs concurrents comme sur un serveur).
_IS_ANDROID = any(k in os.environ for k in ("ANDROID_ARGUMENT", "ANDROID_ROOT", "ANDROID_DATA"))
if _IS_ANDROID:
    _MP_START_METHOD = None
_MP_CTX = mp.get_context(_MP_START_METHOD) if _MP_START_METHOD else None


def _isolated_worker(target, args, kwargs, result_queue) -> None:
    try:
        result_queue.put(("ok", target(*args, **kwargs)))
    except Exception as e:  # noqa: BLE001 — on relaie l'erreur telle quelle au process parent
        result_queue.put(("error", e))


def run_isolated(target, *args, timeout: float = REQUEST_TIMEOUT_SECONDS, **kwargs):
    """Exécute target(*args, **kwargs) avec une vraie coupure au bout de `timeout`
    secondes (voir la note ci-dessus). Lève concurrent.futures.TimeoutError si le
    délai est dépassé, pour rester compatible avec le code d'erreur existant des
    endpoints (HTTP 422, message « trop complexe »)."""
    if _MP_CTX is None:
        # Repli (Android/Chaquopy, ou plateformes sans fork/spawn) : pas de
        # coupure forcée possible sans un vrai processus à tuer, mais on isole
        # au moins chaque appel dans son propre exécuteur à usage unique
        # plutôt que de partager un pool fixe où les threads bloqués
        # s'accumulent. Important : shutdown(wait=False) et non un simple
        # `with` — un `with` attendrait la fin du thread avant de laisser
        # remonter le TimeoutError, ce qui annulerait justement la coupure.
        one_shot = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = one_shot.submit(target, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        finally:
            one_shot.shutdown(wait=False)

    result_queue = _MP_CTX.Queue()
    proc = _MP_CTX.Process(target=_isolated_worker, args=(target, args, kwargs, result_queue))
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        if proc.is_alive():
            proc.kill()
            proc.join()
        raise concurrent.futures.TimeoutError()

    if not result_queue.empty():
        status, payload = result_queue.get()
        if status == "error":
            raise payload
        return payload

    # Le process s'est terminé sans rien renvoyer (crash bas niveau imprévu,
    # ex. segfault d'une dépendance native) : on le signale explicitement
    # plutôt que de laisser l'appelant deviner pourquoi il n'y a pas de résultat.
    raise RuntimeError("Le calcul a échoué de manière inattendue (processus interrompu).")

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 Mo, suffisant pour une photo de cahier compressée


class CorrectionRequest(BaseModel):
    function_str: str
    exercise_title: str = "Étude de fonction"


class EquationRequest(BaseModel):
    equation_str: str
    exercise_title: str = "Résolution d'équation"


class InequalityRequest(BaseModel):
    inequality_str: str
    exercise_title: str = "Résolution d'inéquation"


class SystemRequest(BaseModel):
    equations: list  # liste de chaines "a*x + b*y + ... = c" — 2, 3, 4 equations
    exercise_title: str = "Résolution de système"


class IntegralRequest(BaseModel):
    function_str: str
    a_str: Optional[str] = None  # borne inferieure ; absente => primitive seule
    b_str: Optional[str] = None  # borne superieure
    exercise_title: str = "Calcul intégral"


class SequenceRequest(BaseModel):
    first_term_str: str
    recurrence_str: str
    start_index: int = 0
    exercise_title: str = "Étude de suite"


class BinomialRequest(BaseModel):
    n: int
    p_str: str
    k: Optional[int] = None
    exercise_title: str = "Loi binomiale"


class ComplexRequest(BaseModel):
    z_str: str
    exercise_title: str = "Étude d'un nombre complexe"


class MatrixRequest(BaseModel):
    rows: list
    exercise_title: str = "Étude d'une matrice"


class MatrixOperationRequest(BaseModel):
    rows_a: list
    rows_b: list
    operation: str  # "somme" | "produit"
    exercise_title: str = "Opération matricielle"


class GeometryRequest(BaseModel):
    A: list
    B: list
    C: Optional[list] = None
    exercise_title: str = "Géométrie analytique"


class ChemistryRequest(BaseModel):
    equation_str: str
    exercise_title: str = "Équilibrage d'équation chimique"


class CircuitRequest(BaseModel):
    resistances: list
    topology: str  # "série" | "parallèle"
    voltage: str
    exercise_title: str = "Circuit électrique"


class KinematicsRequest(BaseModel):
    x0: str
    v0: str
    a: str
    t: str
    exercise_title: str = "Cinématique (MRUV)"


class OpticsRequest(BaseModel):
    f: str
    OA: str
    exercise_title: str = "Optique — lentille mince convergente"


class StoichiometryRequest(BaseModel):
    equation_str: str
    known_compound: str
    amount: str
    amount_type: str  # "mol" | "g"
    exercise_title: str = "Stœchiométrie"


class ThermodynamicsRequest(BaseModel):
    mode: str  # "sensible" | "latente"
    mass: str
    specific_heat: Optional[str] = None
    t_initial: Optional[str] = None
    t_final: Optional[str] = None
    latent_heat: Optional[str] = None
    exercise_title: str = "Calorimétrie"


@app.get("/api/health")
def health():
    return {
        "status": "ok", "engine": "sympy", "llm_used": False,
        "ocr": "tesseract" if OCR_AVAILABLE else None,
    }


def _task_correct(req: CorrectionRequest):
    analysis = analyze(req.function_str)
    return write_correction(req.exercise_title, req.function_str, analysis)


@app.post("/api/correct")
def correct(req: CorrectionRequest):
    try:
        correction = run_isolated(_task_correct, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette fonction est trop complexe pour être analysée automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_solve_equation_endpoint(req: EquationRequest):
    analysis = solve_equation(req.equation_str)
    return write_equation_correction(req.exercise_title, req.equation_str, analysis)


@app.post("/api/solve-equation")
def solve_equation_endpoint(req: EquationRequest):
    try:
        correction = run_isolated(_task_solve_equation_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette équation est trop complexe pour être résolue automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_solve_inequality_endpoint(req: InequalityRequest):
    analysis = solve_inequality(req.inequality_str)
    return write_inequality_correction(req.exercise_title, req.inequality_str, analysis)


@app.post("/api/solve-inequality")
def solve_inequality_endpoint(req: InequalityRequest):
    try:
        correction = run_isolated(_task_solve_inequality_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette inéquation est trop complexe pour être résolue automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_solve_system_endpoint(req: SystemRequest):
    analysis = solve_system(req.equations)
    return write_system_correction(req.exercise_title, req.equations, analysis)


@app.post("/api/solve-system")
def solve_system_endpoint(req: SystemRequest):
    try:
        correction = run_isolated(_task_solve_system_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce système est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_integral_endpoint(req: IntegralRequest):
    analysis = analyze_integral(req.function_str, req.a_str, req.b_str)
    return write_integral_correction(req.exercise_title, req.function_str, analysis)


@app.post("/api/analyze-integral")
def analyze_integral_endpoint(req: IntegralRequest):
    try:
        correction = run_isolated(_task_analyze_integral_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul intégral est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_sequence_endpoint(req: SequenceRequest):
    analysis = analyze_sequence(req.first_term_str, req.recurrence_str, req.start_index)
    return write_sequence_correction(req.exercise_title, req.first_term_str, req.recurrence_str, analysis)


@app.post("/api/analyze-sequence")
def analyze_sequence_endpoint(req: SequenceRequest):
    try:
        correction = run_isolated(_task_analyze_sequence_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette suite est trop complexe pour être étudiée automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_binomial_endpoint(req: BinomialRequest):
    analysis = analyze_binomial(req.n, req.p_str, req.k)
    return write_binomial_correction(req.exercise_title, req.n, req.p_str, req.k, analysis)


@app.post("/api/analyze-binomial")
def analyze_binomial_endpoint(req: BinomialRequest):
    try:
        correction = run_isolated(_task_analyze_binomial_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_complex_endpoint(req: ComplexRequest):
    analysis = analyze_complex(req.z_str)
    return write_complex_correction(req.exercise_title, req.z_str, analysis)


@app.post("/api/analyze-complex")
def analyze_complex_endpoint(req: ComplexRequest):
    try:
        correction = run_isolated(_task_analyze_complex_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_matrix_endpoint(req: MatrixRequest):
    analysis = analyze_matrix(req.rows)
    label = "M = " + str(req.rows)
    return write_matrix_correction(req.exercise_title, label, analysis)


@app.post("/api/analyze-matrix")
def analyze_matrix_endpoint(req: MatrixRequest):
    try:
        correction = run_isolated(_task_analyze_matrix_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_matrix_operation_endpoint(req: MatrixOperationRequest):
    result = compute_matrix_operation(req.rows_a, req.rows_b, req.operation)
    label = f"{req.operation}({req.rows_a}, {req.rows_b})"
    return write_matrix_operation_correction(req.exercise_title, label, result)


@app.post("/api/matrix-operation")
def matrix_operation_endpoint(req: MatrixOperationRequest):
    try:
        correction = run_isolated(_task_matrix_operation_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette opération est trop complexe pour être résolue automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_geometry_endpoint(req: GeometryRequest):
    analysis = analyze_geometry(req.A, req.B, req.C)
    label = f"A={req.A}, B={req.B}" + (f", C={req.C}" if req.C else "")
    return write_geometry_correction(req.exercise_title, label, analysis)


@app.post("/api/analyze-geometry")
def analyze_geometry_endpoint(req: GeometryRequest):
    try:
        correction = run_isolated(_task_analyze_geometry_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_balance_equation_endpoint(req: ChemistryRequest):
    analysis = balance_equation(req.equation_str)
    return write_chemistry_correction(req.exercise_title, req.equation_str, analysis)


@app.post("/api/balance-equation")
def balance_equation_endpoint(req: ChemistryRequest):
    try:
        correction = run_isolated(_task_balance_equation_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette équation est trop complexe pour être équilibrée automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_circuit_endpoint(req: CircuitRequest):
    analysis = analyze_circuit(req.resistances, req.topology, req.voltage)
    label = f"{req.topology}({req.resistances}, U={req.voltage})"
    return write_circuit_correction(req.exercise_title, label, analysis)


@app.post("/api/analyze-circuit")
def analyze_circuit_endpoint(req: CircuitRequest):
    try:
        correction = run_isolated(_task_analyze_circuit_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce circuit est trop complexe pour être analysé automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_kinematics_endpoint(req: KinematicsRequest):
    analysis = analyze_kinematics(req.x0, req.v0, req.a, req.t)
    label = f"x0={req.x0}, v0={req.v0}, a={req.a}, t={req.t}"
    return write_kinematics_correction(req.exercise_title, label, analysis)


@app.post("/api/analyze-kinematics")
def analyze_kinematics_endpoint(req: KinematicsRequest):
    try:
        correction = run_isolated(_task_analyze_kinematics_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce mouvement est trop complexe pour être analysé automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_optics_endpoint(req: OpticsRequest):
    analysis = analyze_thin_lens(req.f, req.OA)
    label = f"f'={req.f}, OA={req.OA}"
    return write_optics_correction(req.exercise_title, label, analysis)


@app.post("/api/analyze-optics")
def analyze_optics_endpoint(req: OpticsRequest):
    try:
        correction = run_isolated(_task_analyze_optics_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_stoichiometry_endpoint(req: StoichiometryRequest):
    analysis = analyze_stoichiometry(req.equation_str, req.known_compound, req.amount, req.amount_type)
    return write_stoichiometry_correction(
        req.exercise_title, req.equation_str, req.known_compound, req.amount, req.amount_type, analysis
    )


@app.post("/api/analyze-stoichiometry")
def analyze_stoichiometry_endpoint(req: StoichiometryRequest):
    try:
        correction = run_isolated(_task_analyze_stoichiometry_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_analyze_thermodynamics_endpoint(req: ThermodynamicsRequest):
    if req.mode == "sensible":
        if not all([req.specific_heat, req.t_initial, req.t_final]):
            raise ValueError("Le mode « sensible » requiert specific_heat, t_initial et t_final.")
        analysis = analyze_sensible_heat(req.mass, req.specific_heat, req.t_initial, req.t_final)
    elif req.mode == "latente":
        if not req.latent_heat:
            raise ValueError("Le mode « latente » requiert latent_heat.")
        analysis = analyze_latent_heat(req.mass, req.latent_heat)
    else:
        raise ValueError(f"Mode inconnu : « {req.mode} » (attendu : « sensible » ou « latente »).")
    return write_thermodynamics_correction(req.exercise_title, f"{req.mode}({req.mass})", analysis)


@app.post("/api/analyze-thermodynamics")
def analyze_thermodynamics_endpoint(req: ThermodynamicsRequest):
    try:
        correction = run_isolated(_task_analyze_thermodynamics_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce calcul est trop complexe pour être résolu automatiquement dans le temps imparti.",
        )
    return correction_to_dict(correction)


def _task_ocr(image_bytes: bytes, suffix: str):
    """Isolé dans son propre processus, comme tous les autres calculs (voir
    run_isolated) — et pour une raison supplémentaire ici, propre à l'OCR :
    ces deux endpoints étaient déclarés `async def` alors que extract_text /
    extract_line_candidates sont des fonctions 100% synchrones et lourdes
    (OpenCV + Tesseract). Sous FastAPI, le code d'un `async def` s'exécute
    directement sur la boucle d'événements asyncio : un traitement d'image
    bloquant exécuté là ne bloque pas que CETTE requête, il gèle TOUT le
    serveur (donc toutes les autres requêtes, même sans rapport, pendant
    toute la durée du traitement). Les repasser par run_isolated corrige ce
    gel ET leur donne, comme au reste de l'API, une vraie coupure au bout du
    délai imparti si une image pathologique faisait ramer OpenCV/Tesseract.
    """
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp.flush()
        try:
            raw_text = extract_text(tmp.name, single_line=True)
        except OcrUnavailableError:
            raise  # laisser remonter tel quel, distinct d'une simple erreur de lecture
        except Exception as e:
            raise RuntimeError(f"Lecture de l'image impossible : {e}")

    cleaned = clean_text(raw_text)
    parse_error = None
    canonical = None
    try:
        canonical = to_canonical_expression(raw_text)
    except OcrParseError as e:
        parse_error = str(e)

    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned,
        "suggested_function_str": canonical,  # None si le parsing a échoué
        "parse_error": parse_error,
        "note": (
            "Vérifiez toujours ce texte avant de lancer la correction : l'OCR "
            "généraliste confond parfois « ^ » (exposant) avec « * »."
        ),
    }


@app.post("/api/ocr")
async def ocr(image: UploadFile = File(...)):
    """Extrait le texte d'une photo/scan d'énoncé. Renvoie TOUJOURS le texte brut ET
    une proposition d'expression nettoyée pour confirmation/édition par l'utilisateur
    côté frontend — jamais envoyé directement au moteur de correction sans validation.

    Limite honnête (voir README) : Tesseract est un OCR généraliste, pas spécialisé
    maths. Le caractère « ^ » (exposant) est fréquemment mal lu (confondu avec « * »)
    sur du texte imprimé compact. Une photo nette, texte imprimé sur une seule ligne,
    fonctionne raisonnablement ; l'écriture manuscrite ou les fractions empilées non.
    """
    content = await image.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image trop volumineuse (max 8 Mo).")

    suffix = Path(image.filename or "upload.png").suffix or ".png"
    try:
        return run_isolated(_task_ocr, content, suffix)
    except OcrUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette image est trop longue à analyser dans le temps imparti.",
        )


def _task_ocr_page(image_bytes: bytes, suffix: str):
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp.flush()
        try:
            candidates = extract_line_candidates(tmp.name)
        except OcrUnavailableError:
            raise
        except Exception as e:
            raise RuntimeError(f"Lecture de l'image impossible : {e}")

    enriched = []
    for c in candidates:
        cleaned = clean_text(c["text"])
        suggested, parse_error = None, None
        try:
            suggested = to_canonical_expression(c["text"])
        except OcrParseError as e:
            parse_error = str(e)
        enriched.append({
            "raw_text": c["text"],
            "cleaned_text": cleaned,
            "math_likelihood": c["score"],
            "suggested_function_str": suggested,
            "parse_error": parse_error,
            "bbox": c["bbox"],
        })

    return {
        "candidates": enriched,
        "note": (
            "Plusieurs lignes ont été détectées sur la photo ; la plus probable est "
            "en tête de liste, mais vérifiez toujours avant de lancer la correction."
        ),
    }


@app.post("/api/ocr-page")
async def ocr_page(image: UploadFile = File(...)):
    """Pour une photo pleine page (énoncé pas pré-recadré) : détecte toutes les
    lignes de texte et les classe par vraisemblance d'être l'expression
    mathématique recherchée (plutôt qu'une consigne ou du texte environnant).
    Ne choisit jamais à la place de l'utilisateur — renvoie les meilleurs
    candidats, chacun passé au même nettoyage/parsing que /api/ocr, pour
    sélection et confirmation côté frontend."""
    content = await image.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image trop volumineuse (max 8 Mo).")

    suffix = Path(image.filename or "upload.png").suffix or ".png"
    try:
        return run_isolated(_task_ocr_page, content, suffix)
    except OcrUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Cette image est trop longue à analyser dans le temps imparti.",
        )


def _task_plot_data_endpoint(req: CorrectionRequest):
    analysis = analyze(req.function_str)
    return plot_function_analysis_data(analysis, req.function_str)


@app.post("/api/plot-data")
def plot_data_endpoint(req: CorrectionRequest):
    """Version JSON du graphique (mêmes données que /api/plot, mais pour un
    rendu interactif côté frontend au lieu d'une image PNG statique)."""
    try:
        data = run_isolated(_task_plot_data_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce graphique est trop complexe pour être généré automatiquement dans le temps imparti.",
        )
    return data


def _task_plot_endpoint(req: CorrectionRequest):
    analysis = analyze(req.function_str)
    return plot_function_analysis_bytes(analysis, req.function_str)


@app.post("/api/plot")
def plot_endpoint(req: CorrectionRequest):
    try:
        png_bytes = run_isolated(_task_plot_endpoint, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except concurrent.futures.TimeoutError:
        raise HTTPException(
            status_code=422,
            detail="Ce graphique est trop complexe pour être généré automatiquement dans le temps imparti.",
        )
    return Response(content=png_bytes, media_type="image/png")


@app.post("/api/export-pdf")
def export_pdf_endpoint(correction: dict):
    """Reçoit le dict de correction déjà calculé (tel que renvoyé par n'importe lequel
    des endpoints /api/correct, /api/solve-equation, etc. — le frontend le renvoie tel
    quel après un premier appel) et produit un PDF téléchargeable. Générique sur les
    6 types d'exercice : le rendu ne dépend que de la structure Step/Correction, pas
    du type d'exercice d'origine."""
    if "steps" not in correction:
        raise HTTPException(status_code=400, detail="Correction invalide : champ 'steps' manquant.")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    try:
        export_correction_to_pdf(correction, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec de la génération du PDF : {e}")
    filename = (correction.get("exercise_title") or "correction").replace(" ", "_").replace("/", "-") + ".pdf"
    return FileResponse(tmp.name, media_type="application/pdf", filename=filename)


@app.post("/api/export-docx")
def export_docx_endpoint(correction: dict):
    """Même principe que /api/export-pdf, pour un document Word."""
    if "steps" not in correction:
        raise HTTPException(status_code=400, detail="Correction invalide : champ 'steps' manquant.")
    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.close()
    try:
        export_correction_to_docx(correction, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec de la génération du DOCX : {e}")
    filename = (correction.get("exercise_title") or "correction").replace(" ", "_").replace("/", "-") + ".docx"
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@app.get("/api/thermodynamics-examples")
def thermodynamics_examples():
    return [
        {"title": "Chauffer 500g d'eau (20→100°C)", "mode": "sensible", "mass": "500", "specific_heat": "4.18", "t_initial": "20", "t_final": "100"},
        {"title": "Refroidir 200g d'eau (80→20°C)", "mode": "sensible", "mass": "200", "specific_heat": "4.18", "t_initial": "80", "t_final": "20"},
        {"title": "Vaporiser 100g d'eau", "mode": "latente", "mass": "100", "latent_heat": "2257"},
    ]


@app.get("/api/stoichiometry-examples")
def stoichiometry_examples():
    return [
        {"title": "Combustion du méthane (16g CH4)", "equation_str": "CH4 + O2 -> CO2 + H2O", "known_compound": "CH4", "amount": "16", "amount_type": "g"},
        {"title": "Formation de l'eau (2 mol H2)", "equation_str": "H2 + O2 -> H2O", "known_compound": "H2", "amount": "2", "amount_type": "mol"},
    ]


@app.get("/api/optics-examples")
def optics_examples():
    return [
        {"title": "Image réelle (objet loin)", "f": "10", "OA": "-30"},
        {"title": "Loupe (objet proche)", "f": "10", "OA": "-5"},
    ]


@app.get("/api/kinematics-examples")
def kinematics_examples():
    return [
        {"title": "Freinage (décélération)", "x0": "0", "v0": "20", "a": "-2", "t": "3"},
        {"title": "Accélération depuis l'arrêt", "x0": "0", "v0": "0", "a": "2", "t": "5"},
        {"title": "Chute libre (g=9.8)", "x0": "0", "v0": "0", "a": "9.8", "t": "2"},
    ]


@app.get("/api/circuit-examples")
def circuit_examples():
    return [
        {"title": "3 résistances en série", "resistances": ["10", "20", "30"], "topology": "série", "voltage": "12"},
        {"title": "3 résistances en parallèle", "resistances": ["10", "20", "30"], "topology": "parallèle", "voltage": "12"},
    ]


@app.get("/api/chemistry-examples")
def chemistry_examples():
    return [
        {"title": "Formation de l'eau", "equation_str": "H2 + O2 -> H2O"},
        {"title": "Combustion du méthane", "equation_str": "CH4 + O2 -> CO2 + H2O"},
        {"title": "Oxydation de l'aluminium", "equation_str": "Al + O2 -> Al2O3"},
        {"title": "Réduction de l'oxyde de fer", "equation_str": "Fe2O3 + CO -> Fe + CO2"},
    ]


@app.get("/api/geometry-examples")
def geometry_examples():
    return [
        {"title": "Triangle rectangle en A", "A": [0, 0], "B": [1, 0], "C": [0, 1]},
        {"title": "Points alignés", "A": [0, 0], "B": [1, 1], "C": [2, 2]},
        {"title": "Distance/milieu simple", "A": [1, 2], "B": [4, 6], "C": None},
    ]


@app.get("/api/matrix-examples")
def matrix_examples():
    return [
        {"title": "2×2 inversible", "rows": [["1", "2"], ["3", "4"]]},
        {"title": "3×3 singulière", "rows": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "0"]]},
    ]


@app.get("/api/complex-examples")
def complex_examples():
    return [
        {"title": "1 + i (angle remarquable)", "z_str": "1 + I"},
        {"title": "3 + 4i", "z_str": "3 + 4*I"},
        {"title": "-1 - i√3", "z_str": "-1 - I*sqrt(3)"},
    ]


@app.get("/api/binomial-examples")
def binomial_examples():
    return [
        {"title": "B(5, 1/3), k=2", "n": 5, "p_str": "1/3", "k": 2},
        {"title": "B(10, 0.2), k=3", "n": 10, "p_str": "0.2", "k": 3},
        {"title": "B(6, 0.4), k=3", "n": 6, "p_str": "0.4", "k": 3},
    ]


@app.get("/api/sequence-examples")
def sequence_examples():
    return [
        {"title": "Arithmétique", "first_term_str": "2", "recurrence_str": "u + 3"},
        {"title": "Géométrique (convergente)", "first_term_str": "10", "recurrence_str": "0.5*u"},
        {"title": "Géométrique (divergente)", "first_term_str": "3", "recurrence_str": "2*u"},
        {"title": "Arithmético-géométrique", "first_term_str": "1", "recurrence_str": "2*u + 3"},
    ]


@app.get("/api/system-examples")
def system_examples():
    raw = [
        {"title": "Solution unique (2 inconnues)", "equations": ["2*x + y = 5", "x - y = 1"]},
        {"title": "Aucune solution", "equations": ["2*x + y = 5", "2*x + y = 3"]},
        {"title": "Infinité de solutions", "equations": ["2*x + y = 5", "4*x + 2*y = 10"]},
        {"title": "3 inconnues (x, y, z)", "equations": ["x + y + z = 6", "2*x - y + z = 3", "x - y - z = -4"]},
    ]
    for e in raw:
        e["displays"] = [to_display(eq) for eq in e["equations"]]
    return raw


@app.get("/api/integral-examples")
def integral_examples():
    raw = [
        {"title": "Primitive d'un polynôme", "function_str": "x**2 + 3*x", "a_str": "", "b_str": ""},
        {"title": "Primitive avec exp/log", "function_str": "exp(x) + 1/x", "a_str": "", "b_str": ""},
        {"title": "Aire sous x² sur [0, 3]", "function_str": "x**2", "a_str": "0", "b_str": "3"},
        {"title": "Aire avec sinus sur [0, π]", "function_str": "sin(x)", "a_str": "0", "b_str": "pi"},
    ]
    for e in raw:
        e["display"] = to_display(e["function_str"])
    return raw


@app.get("/api/inequality-examples")
def inequality_examples():
    raw = [
        {"title": "Linéaire", "inequality_str": "2*x - 4 > 0"},
        {"title": "Quadratique (Δ > 0)", "inequality_str": "x**2 - 5*x + 6 > 0"},
        {"title": "Quadratique (Δ = 0)", "inequality_str": "x**2 - 4*x + 4 <= 0"},
        {"title": "Quadratique (Δ < 0)", "inequality_str": "x**2 + x + 1 > 0"},
        {"title": "Avec racine carrée", "inequality_str": "sqrt(x + 1) < x - 1"},
    ]
    for e in raw:
        e["display"] = to_display(e["inequality_str"])
    return raw


@app.get("/api/equation-examples")
def equation_examples():
    raw = [
        {"title": "Linéaire", "equation_str": "2*x + 4 = 0"},
        {"title": "Quadratique (Δ > 0)", "equation_str": "x**2 - 5*x + 6 = 0"},
        {"title": "Quadratique (Δ = 0)", "equation_str": "x**2 - 4*x + 4 = 0"},
        {"title": "Quadratique (Δ < 0)", "equation_str": "x**2 + x + 1 = 0"},
        {"title": "Degré 3", "equation_str": "x**3 - 8 = 0"},
        {"title": "Avec racine carrée", "equation_str": "sqrt(2*x + 1) = x - 1"},
        {"title": "Avec racine cubique", "equation_str": "x**(1/3) = 2"},
    ]
    for e in raw:
        e["display"] = to_display(e["equation_str"])
    return raw


@app.get("/api/examples")
def examples():
    """Quelques fonctions prêtes à l'emploi pour tester rapidement le front."""
    raw = [
        {"title": "Polynôme du 3e degré", "function_str": "x**3 - 3*x + 2"},
        {"title": "Fraction rationnelle", "function_str": "(2*x + 1)/(x - 1)"},
        {"title": "Fonction paire", "function_str": "x**4 - 2*x**2"},
        {"title": "Exponentielle", "function_str": "exp(x) - 2"},
        {"title": "Logarithme", "function_str": "log(x)"},
        {"title": "Trigonométrique (sinus)", "function_str": "sin(x)"},
        {"title": "Valeur absolue", "function_str": "Abs(x - 2)"},
        {"title": "Racine carrée au numérateur", "function_str": "sqrt(x)/(x - 1)"},
        {"title": "Racine carrée au dénominateur", "function_str": "1/sqrt(x - 2)"},
        {"title": "Fonction par morceaux", "function_str": "Piecewise((x**2, x < 1), (2*x - 1, True))"},
    ]
    for e in raw:
        e["display"] = to_display(e["function_str"])
    return raw


class HistoryEntryRequest(BaseModel):
    exercise_type: str
    exercise_type_label: str
    title: str
    summary: str
    payload: dict
    score: Optional[int] = None
    score_max: Optional[int] = None


@app.post("/api/history")
def save_history_entry(req: HistoryEntryRequest):
    """Enregistre une correction dans l'historique local (SQLite). Appelé
    automatiquement par le frontend après chaque correction affichée."""
    entry_id = history_store.save_entry(
        exercise_type=req.exercise_type,
        exercise_type_label=req.exercise_type_label,
        title=req.title,
        summary=req.summary,
        payload=req.payload,
        score=req.score,
        score_max=req.score_max,
    )
    return {"id": entry_id}


@app.get("/api/history")
def list_history(limit: int = 200):
    return {"entries": history_store.list_entries(limit=limit)}


@app.get("/api/history/{entry_id}")
def get_history_entry(entry_id: int):
    entry = history_store.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrée d'historique introuvable.")
    return entry


@app.delete("/api/history/{entry_id}")
def delete_history_entry(entry_id: int):
    deleted = history_store.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrée d'historique introuvable.")
    return {"deleted": True}


@app.delete("/api/history")
def clear_history():
    count = history_store.clear_all()
    return {"deleted_count": count}


# IMPORTANT : ce mount doit rester la toute dernière ligne du fichier. StaticFiles
# capte "/" et tout ce qui n'est pas déjà une route déclarée au-dessus — le déclarer
# avant les routes /api/... les rendrait inaccessibles (FastAPI/Starlette résout
# dans l'ordre de déclaration). Grâce à ça, une seule commande (`uvicorn app:app`)
# suffit : ouvrir http://localhost:8000 sert directement le frontend.
_frontend_dir = Path(__file__).parent / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
