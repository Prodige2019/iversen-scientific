"""
Démo Phase 1 — aucune dépendance à une API IA cloud.
Lance : python3 demo.py
"""
from engine import analyze, write_correction, render_text, render_markdown

EXERCISES = [
    ("Exercice 3 — Étude de fonction", "x**3 - 3*x + 2"),
    ("Exercice — fonction rationnelle", "(2*x + 1)/(x - 1)"),
    ("Exercice — fonction paire", "x**4 - 2*x**2"),
    ("Exercice — exponentielle", "exp(x) - 2"),
    ("Exercice — logarithme", "log(x)"),
    ("Exercice — trigonométrique", "sin(x)"),
    ("Exercice — valeur absolue", "Abs(x - 2)"),
    ("Exercice — fonction par morceaux", "Piecewise((x**2, x < 1), (2*x - 1, True))"),
]

if __name__ == "__main__":
    for title, f_str in EXERCISES:
        analysis = analyze(f_str)
        correction = write_correction(title, f_str, analysis)
        print(render_text(correction))
        print("\n" + "=" * 70 + "\n")

    # Export d'un exemple en Markdown pour vérification visuelle
    analysis = analyze(EXERCISES[0][1])
    correction = write_correction(EXERCISES[0][0], EXERCISES[0][1], analysis)
    with open("correction_exemple.md", "w", encoding="utf-8") as f:
        f.write(render_markdown(correction))
    print("→ correction_exemple.md généré")
