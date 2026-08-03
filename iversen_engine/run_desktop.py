"""
Point d'entrée pour les versions "bureau" (Windows .exe / macOS .app-.dmg)
fabriquées avec PyInstaller — voir GUIDE_INSTALLATION_ET_COMPILATION.txt.
Ce fichier ne contient aucune logique métier : il démarre simplement le même
serveur FastAPI que d'habitude (app.py), et ouvre le navigateur dessus
automatiquement, pour qu'un utilisateur qui double-clique sur l'exécutable
n'ait aucune commande à taper.
Utilisation normale (développement) : inutile, on lance directement
`uvicorn app:app` ou `python start.py` comme d'habitude.
Utilisation ciblée par ce fichier : uniquement une fois empaqueté par
PyInstaller (voir PARTIE 2 et PARTIE 3 du guide d'installation).
"""
import sys
import io

# En mode --windowed (PyInstaller), il n'y a aucune console : sys.stdout et
# sys.stderr valent None. Uvicorn appelle .isatty() dessus au demarrage et
# plante immediatement si c'est le cas ("Unable to configure formatter
# 'default' ... 'NoneType' object has no attribute 'isatty'"). On les
# remplace par un flux neutre avant tout le reste, pour que ca ne se
# produise jamais, que l'app tourne avec ou sans console.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import threading
import time
import webbrowser
import uvicorn
from app import app


def _open_browser_when_ready():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
