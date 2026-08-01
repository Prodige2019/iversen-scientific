#!/usr/bin/env python3
"""
Lancement en une seule commande — pensé pour quelqu'un qui découvre le projet.

Utilisation :
    python3 start.py

Ce script :
1. vérifie que Python est assez récent
2. crée un environnement virtuel isolé (.venv) s'il n'existe pas déjà — cela évite
   les erreurs d'installation sur les systèmes Python récents (Ubuntu/Debian
   « externally managed environment »), et n'installe jamais rien au niveau du
   système : tout reste contenu dans le dossier du projet
3. installe les dépendances Python dans cet environnement
4. vérifie que Tesseract (OCR) est installé, avec des instructions claires sinon
5. démarre le serveur
6. ouvre automatiquement le navigateur sur l'application

Aucune action destructrice : pas de suppression de fichiers, pas de modification
du système au-delà du dossier .venv créé à côté de ce script.
"""
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
VENV_DIR = ROOT / ".venv"
PORT = 8000


def step(msg: str) -> None:
    print(f"\n▶ {msg}")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def check_python_version() -> None:
    step("Vérification de la version de Python…")
    if sys.version_info < (3, 9):
        print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor} détecté. "
              f"Ce projet nécessite Python 3.9 ou plus récent.")
        print("  Installez une version récente depuis https://python.org, puis relancez ce script.")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def ensure_venv() -> None:
    step("Vérification de l'environnement virtuel du projet (.venv)…")
    if venv_python().exists():
        print("✓ Environnement déjà présent.")
        return
    print("  Première utilisation : création d'un environnement isolé (une seule fois)…")
    result = subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if result.returncode != 0:
        print("✗ Impossible de créer l'environnement virtuel.")
        print("  Essayez d'installer le paquet correspondant : sur Debian/Ubuntu, "
              "`sudo apt-get install python3-venv`, puis relancez ce script.")
        sys.exit(1)
    print("✓ Environnement créé.")


def check_tesseract() -> None:
    step("Vérification de Tesseract (OCR, pour la lecture de photos)…")
    if shutil.which("tesseract"):
        print("✓ Tesseract trouvé — la fonctionnalité photo sera disponible.")
        return
    print("✗ Tesseract n'est pas installé. Le reste de l'application fonctionnera "
          "quand même (fonctions, équations, etc.), mais pas la lecture de photos.")
    print("  Pour l'installer :")
    print("    - Ubuntu / Debian :  sudo apt-get install tesseract-ocr")
    print("    - macOS (Homebrew) : brew install tesseract")
    print("    - Windows :          https://github.com/UB-Mannheim/tesseract/wiki")
    print("  Vous pouvez relancer ce script après l'installation, ou continuer sans OCR.")
    time.sleep(2)


def install_python_dependencies() -> None:
    step("Installation des dépendances Python dans l'environnement du projet "
         "(peut prendre 1 à 2 minutes la première fois)…")
    requirements = ROOT / "requirements.txt"
    if not requirements.exists():
        print(f"✗ Fichier introuvable : {requirements}")
        sys.exit(1)
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-q", "--upgrade", "pip"],
        cwd=str(ROOT),
    )
    result = subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-q", "-r", str(requirements)],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print("✗ L'installation des dépendances a échoué. Essayez manuellement :")
        print(f"    {venv_python()} -m pip install -r requirements.txt")
        sys.exit(1)
    print("✓ Dépendances installées.")


def start_server_and_open_browser() -> None:
    step(f"Démarrage du serveur sur http://localhost:{PORT} …")
    process = subprocess.Popen(
        [str(venv_python()), "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=str(ROOT),
    )
    time.sleep(2.5)
    url = f"http://localhost:{PORT}"
    print(f"✓ Serveur lancé. Ouverture de {url} dans le navigateur…")
    try:
        webbrowser.open(url)
    except Exception:
        print(f"  (impossible d'ouvrir le navigateur automatiquement — ouvrez {url} vous-même)")

    print("\n" + "=" * 60)
    print("  Iversen Scientific est en ligne : " + url)
    print("  Laissez cette fenêtre ouverte tant que vous utilisez l'application.")
    print("  Pour arrêter : fermez cette fenêtre ou appuyez sur Ctrl+C.")
    print("=" * 60 + "\n")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nArrêt du serveur…")
        process.terminate()


if __name__ == "__main__":
    print("=" * 60)
    print("  Iversen Scientific — démarrage")
    print("=" * 60)
    check_python_version()
    ensure_venv()
    install_python_dependencies()
    check_tesseract()
    start_server_and_open_browser()
