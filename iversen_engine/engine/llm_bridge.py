"""
Point d'extension optionnel — enrichissement du phrasé par un LLM open-source LOCAL.

Ce module est volontairement un simple contrat d'interface : rien n'est appelé par
défaut, et le moteur de correction fonctionne intégralement sans lui (voir writer.py).
Le rôle d'un LLM ici serait UNIQUEMENT de reformuler le texte pédagogique déjà généré
(le rendre plus naturel, l'adapter au niveau de l'élève) — jamais de recalculer ou de
modifier un résultat mathématique. La séparation stricte calcul (SymPy) / phrasé (LLM)
est ce qui évite les hallucinations sur les résultats.

Exemple d'implémentation possible avec Ollama (https://ollama.com), 100% local :

    import requests

    class OllamaRewriter(ExplanationRewriter):
        def __init__(self, model: str = "qwen2.5:7b-instruct"):
            self.model = model

        def rewrite(self, step_explanation: str, student_level: str = "terminale") -> str:
            prompt = (
                f"Reformule ce texte pédagogique de mathématiques pour un niveau "
                f"{student_level}, sans changer aucun résultat ni aucune valeur "
                f"numérique, juste le style : {step_explanation}"
            )
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            return r.json().get("response", step_explanation)

Modèles open-source adaptés à ce rôle (spécialisés maths ou généralistes solides,
exécutables localement via Ollama / llama.cpp) : Qwen2.5-Math, DeepSeek-Math,
Mistral-7B-Instruct, Llama-3.1-8B-Instruct.

Ce module n'a pas été testé dans cet environnement (pas d'accès réseau à un serveur
Ollama local ni à un hub de modèles depuis ce sandbox) — il documente le contrat
d'intégration pour la suite du projet.
"""
from abc import ABC, abstractmethod


class ExplanationRewriter(ABC):
    """Contrat que toute intégration LLM locale doit respecter."""

    @abstractmethod
    def rewrite(self, step_explanation: str, student_level: str = "terminale") -> str:
        """Reformule un texte pédagogique SANS changer son contenu factuel."""
        raise NotImplementedError


class IdentityRewriter(ExplanationRewriter):
    """Repli par défaut : ne modifie rien. Utilisé tant qu'aucun LLM local n'est branché."""

    def rewrite(self, step_explanation: str, student_level: str = "terminale") -> str:
        return step_explanation
