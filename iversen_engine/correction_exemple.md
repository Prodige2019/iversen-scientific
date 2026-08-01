# Exercice 3 — Étude de fonction
**f(x) = x**3 - 3*x + 2**

### ✅ Étape 1 — Ensemble de définition
$$ D_f = \mathbb{R} $$
On détermine les valeurs de x pour lesquelles l'expression de f est calculable (pas de division par zéro, pas de racine d'un nombre négatif, pas de logarithme d'une valeur négative ou nulle).

### ✅ Étape 2 — Parité
$$ f \text{ est aucune parité particulière} $$
On compare f(-x) à f(x) : si f(-x) = f(x), f est paire (courbe symétrique par rapport à l'axe des ordonnées) ; si f(-x) = -f(x), f est impaire (symétrie par rapport à l'origine).
> **Règle rappelée :** $f paire ⇔ f(-x) = f(x)    f impaire ⇔ f(-x) = -f(x)$

### ✅ Étape 3 — Calcul de la dérivée
$$ f'(x) = 3 x^{2} - 3 $$
On dérive f terme à terme en appliquant les règles usuelles de dérivation.
> **Règle rappelée :** $(x^n)' = n\,x^{n-1} \quad (u+v)' = u' + v' \quad (uv)' = u'v + uv'$

### ✅ Étape 4 — Étude du signe de f' et variations
$$ (-∞, -1] : f' + 0  ·  [-1, 1] : f' - 0  ·  [1, ∞) : f' + 0 $$
Le signe de f' donne le sens de variation de f : f est croissante là où f' est positive, décroissante là où f' est négative.
> **Règle rappelée :** $f' > 0 sur I ⇒ f croissante sur I    f' < 0 sur I ⇒ f décroissante sur I$

### ✅ Étape 5 — Extremums locaux
$$ maximum local en x = -1, f(-1) = 4  ·  minimum local en x = 1, f(1) = 0 $$
Un extremum local apparaît là où f' s'annule en changeant de signe : f' passe de + à - pour un maximum, de - à + pour un minimum.

### ✅ Étape 6 — Point(s) d'inflexion
$$ f''(x) = 6 x \quad \Rightarrow \quad (0, 2) $$
Un point d'inflexion correspond à un changement de convexité, c'est-à-dire à un zéro de f'' où f'' change effectivement de signe (une simple annulation sans changement de signe ne suffit pas).
> ⚠️ **Attention :** Erreur fréquente : conclure à un point d'inflexion dès que f''(x0) = 0, sans vérifier le changement de signe de f''.

### ✅ Étape 7 — Limites aux bornes du domaine
$$ \lim_{x \to -\infty} f(x) = -\infty  ·  \lim_{x \to +\infty} f(x) = \infty $$
On étudie le comportement de f lorsque x tend vers les bornes de son ensemble de définition.

**Note : 20.0/20.0**