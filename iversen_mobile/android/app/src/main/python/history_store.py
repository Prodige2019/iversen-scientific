"""
Historique des exercices corrigés — stockage local, simple, sans dépendance
supplémentaire (sqlite3 fait partie de la bibliothèque standard de Python).

Chaque correction (n'importe quel type d'exercice) est enregistrée avec :
- un résumé (titre, type, score) pour l'affichage en liste
- le résultat complet (JSON) pour pouvoir le réafficher plus tard exactement
  comme il a été rendu la première fois, sans avoir à relancer le calcul

Le fichier de base de données vit dans iversen_engine/data/history.db, créé
automatiquement au premier lancement.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).parent / "data" / "history.db"


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            exercise_type TEXT NOT NULL,
            exercise_type_label TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            score INTEGER,
            score_max INTEGER,
            payload TEXT NOT NULL
        )
        """
    )
    return conn


def save_entry(
    exercise_type: str,
    exercise_type_label: str,
    title: str,
    summary: str,
    payload: dict,
    score: Optional[int] = None,
    score_max: Optional[int] = None,
) -> int:
    """Enregistre une correction. Renvoie l'id attribué."""
    import datetime

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO history
                (created_at, exercise_type, exercise_type_label, title, summary, score, score_max, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.datetime.now().isoformat(timespec="seconds"),
                exercise_type,
                exercise_type_label,
                title,
                summary,
                score,
                score_max,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        return cur.lastrowid


def list_entries(limit: int = 200) -> list:
    """Liste résumée (sans le payload complet, pour rester léger)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, exercise_type, exercise_type_label, title, summary, score, score_max
            FROM history ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_entry(entry_id: int) -> Optional[dict]:
    """Renvoie l'entrée complète, payload inclus (pour réafficher la correction)."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM history WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        entry = dict(row)
        entry["payload"] = json.loads(entry["payload"])
        return entry


def delete_entry(entry_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
        return cur.rowcount > 0


def clear_all() -> int:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM history")
        return cur.rowcount
