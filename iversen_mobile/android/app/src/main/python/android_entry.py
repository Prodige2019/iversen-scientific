"""
Point d'entree Python execute sur le telephone via Chaquopy.
Demarre le vrai serveur FastAPI (app.py, copie depuis iversen_engine/),
exactement le meme moteur que sur desktop.
"""
import threading

import uvicorn

from app import app


def _run_server(port: int) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def start_server_in_background(port: int) -> None:
    thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    thread.start()