"""Sérialisation d'une Correction en structure JSON-compatible (pour l'API)."""
from typing import Any, Dict
from .models import Correction


def correction_to_dict(correction: Correction) -> Dict[str, Any]:
    return {
        "exercise_title": correction.exercise_title,
        "function_str": correction.function_str,
        "subject_line": correction.subject_line,
        "score": correction.score,
        "score_max": correction.score_max,
        "steps": [
            {
                "title": s.title,
                "result_latex": s.result_latex,
                "explanation": s.explanation,
                "rule_recalled": s.rule_recalled,
                "warning": s.warning,
                "is_complete": s.is_complete,
                "weight": s.weight,
            }
            for s in correction.steps
        ],
    }
