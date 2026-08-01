"""
Modèles de données pour une correction pas à pas.
Aucune dépendance IA ici : ce sont de simples structures de données
produites par le moteur symbolique (engine.functions) puis mises en
forme par le rédacteur pédagogique (engine.writer).
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Step:
    title: str                     # ex: "Calcul de la dérivée"
    result_latex: str              # ex: "f'(x) = 3x^{2} - 3"
    explanation: str               # texte pédagogique en français
    rule_recalled: Optional[str] = None   # ex: "(x^n)' = n x^{n-1}"
    warning: Optional[str] = None         # erreur fréquente à signaler
    is_complete: bool = True              # False si étape jugée incomplète (pour la notation)
    weight: float = 1.0                   # importance relative de l'étape dans le barème
                                           # (0 = purement informatif, ne compte pas dans la note)


@dataclass
class Correction:
    exercise_title: str
    function_str: str
    steps: List[Step] = field(default_factory=list)
    score: Optional[float] = None
    score_max: float = 20.0
    subject_line: Optional[str] = None  # override d'affichage (ex: "Équation : ...")

    def add(self, step: Step) -> None:
        self.steps.append(step)

    def compute_score(self) -> float:
        """Notation pondérée : chaque étape a un poids reflétant son importance
        pédagogique (ex: la dérivée pèse plus que la parité). Une étape à poids 0
        est purement informative et ne rentre pas dans le calcul.

        IMPORTANT — honnêteté sur ce que mesure ce score en Phase 1 : le moteur
        génère ici la correction de RÉFÉRENCE (le corrigé), pas une évaluation
        d'une copie d'élève. Le score reflète donc la complétude du corrigé
        généré (proche de 20/20 par construction), pas la performance d'un
        élève. La notation d'une vraie copie (comparaison réponse élève ↔
        corrigé, avec pénalités pour méthode incomplète ou erreur de calcul)
        est prévue en Phase 2/3, une fois l'entrée par photo/OCR en place.
        """
        weighted_steps = [s for s in self.steps if s.weight > 0]
        total_weight = sum(s.weight for s in weighted_steps)
        if total_weight == 0:
            self.score = self.score_max
            return self.score
        earned = sum(s.weight for s in weighted_steps if s.is_complete)
        self.score = round(self.score_max * earned / total_weight, 1)
        return self.score
