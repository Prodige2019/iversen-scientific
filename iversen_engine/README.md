# Iversen Scientific — Moteur de correction Phase 1 + OCR (Phase 2, première itération)

Moteur de correction pas à pas pour l'étude de fonctions (algèbre/analyse, niveau lycée),
**100% open-source, 100% offline, sans appel à une API IA propriétaire**, avec une première
brique de reconnaissance d'énoncé par photo (OCR).

## Pourquoi pas de LLM pour les calculs ?

Un LLM (même open-source) peut se tromper dans un calcul de dérivée ou de limite.
Ici, tous les résultats mathématiques viennent de **SymPy** (bibliothèque Python
open-source de calcul formel) : c'est déterministe, vérifiable, et reproductible.
La rédaction pédagogique (le texte en français façon copie corrigée) est générée
par des templates conditionnels — pas par génération de texte libre — donc elle
reste garantie fidèle aux résultats calculés.

Un point d'extension (`engine/llm_bridge.py`) documente comment brancher plus tard
un LLM open-source **local** (Qwen2.5-Math, Mistral, DeepSeek-Math via Ollama) pour
reformuler le phrasé (adapter au niveau de l'élève, varier le style) — jamais pour
recalculer un résultat. Ce module n'a pas pu être testé dans cet environnement
(pas d'accès réseau à Ollama ou à un hub de modèles depuis ce sandbox), il sert de
spécification pour la suite.

## Structure

```
iversen_engine/
├── engine/
│   ├── functions.py    # moteur symbolique (SymPy) : domaine, parité, dérivées,
│   │                     signe, extrema, inflexion, asymptotes, limites
│   ├── writer.py        # rédaction pédagogique FR (texte + Markdown/LaTeX) — étude de fonction
│   ├── equations.py      # moteur de résolution d'équations (linéaire, quadratique, générale)
│   ├── writer_equations.py  # rédaction pédagogique FR — résolution d'équations
│   ├── inequalities.py    # moteur de résolution d'inéquations (signe du trinôme)
│   ├── writer_inequalities.py  # rédaction pédagogique FR — résolution d'inéquations
│   ├── systems.py          # moteur de résolution de systèmes 2x2 (méthode de substitution)
│   ├── writer_systems.py    # rédaction pédagogique FR — systèmes d'équations
│   ├── sequences.py          # moteur d'étude de suites (arithmétique/géométrique/arithmético-géo)
│   ├── writer_sequences.py    # rédaction pédagogique FR — suites
│   ├── probability.py          # moteur loi binomiale (probabilité exacte, espérance, variance)
│   ├── writer_probability.py    # rédaction pédagogique FR — loi binomiale
│   ├── complex_numbers.py        # moteur nombres complexes (module, argument, formes trig/exp)
│   ├── writer_complex.py          # rédaction pédagogique FR — nombres complexes
│   ├── matrices.py                 # moteur calcul matriciel (déterminant, inverse, somme, produit)
│   ├── writer_matrices.py           # rédaction pédagogique FR — matrices
│   ├── geometry.py                   # moteur géométrie analytique (vecteurs, distances, droites)
│   ├── writer_geometry.py             # rédaction pédagogique FR — géométrie
│   ├── chemistry.py                    # moteur équilibrage d'équations chimiques (nullspace)
│   ├── writer_chemistry.py              # rédaction pédagogique FR — chimie
│   ├── physics_circuits.py               # moteur circuits électriques (série/parallèle, loi d'Ohm)
│   ├── writer_physics_circuits.py         # rédaction pédagogique FR — électricité
│   ├── physics_kinematics.py               # moteur cinématique MRUV (position, vitesse, freinage)
│   ├── writer_physics_kinematics.py         # rédaction pédagogique FR — cinématique
│   ├── physics_optics.py                     # moteur optique (lentille mince convergente)
│   ├── writer_physics_optics.py               # rédaction pédagogique FR — optique
│   ├── chemistry_stoichiometry.py               # moteur stœchiométrie (masses molaires, n=m/M)
│   ├── writer_stoichiometry.py                   # rédaction pédagogique FR — stœchiométrie
│   ├── physics_thermodynamics.py                  # moteur calorimétrie (chaleur sensible/latente)
│   ├── writer_physics_thermodynamics.py            # rédaction pédagogique FR — thermodynamique
│   ├── models.py         # structures Step / Correction + notation pondérée
│   └── llm_bridge.py     # contrat d'extension pour un LLM local (non appelé par défaut)
├── ocr/
│   ├── reader.py         # extraction de texte brut depuis une image (Tesseract)
│   └── normalize.py      # nettoyage texte + parsing tolérant → expression SymPy canonique
├── export_engine/
│   ├── latex_render.py    # rendu LaTeX → PNG (matplotlib mathtext, repli texte brut)
│   ├── pdf_export.py       # assemblage du PDF final (ReportLab, identité visuelle de la maquette)
│   └── docx_export.py       # assemblage du Word final (python-docx, même moteur de formules)
├── plot_engine/
│   └── curve_plot.py       # tracé de courbes (matplotlib), réutilise FunctionAnalysis
├── app.py                 # API FastAPI (/api/correct, /api/ocr, /api/examples)
├── frontend/index.html    # écran web (design de la maquette) : saisie texte OU photo
├── demo.py               # démo sur 8 exercices (polynôme, rationnelle, exp, log, trig, Abs, Piecewise)
├── test_engine.py         # 130 tests unitaires + intégration (moteurs + API + OCR + export + graphique)
└── correction_exemple.md  # sortie générée par demo.py
```

## Démarrage rapide (recommandé)

```bash
python3 start.py
```

Une seule commande : ça crée un environnement isolé, installe tout ce qu'il faut,
démarre le serveur, et ouvre le navigateur automatiquement sur l'application
(frontend + API sur `http://localhost:8000`, servis ensemble par le même serveur —
plus besoin de lancer deux serveurs séparés). Pas à l'aise avec la ligne de
commande ? Suis **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)**, écrit pour un
débutant complet.

## Lancer le moteur seul (ligne de commande, sans interface)

```bash
pip install sympy
python3 demo.py                       # démo sur 8 exercices
python3 -m pytest test_engine.py -v   # tests unitaires
```

## Lancer manuellement (sans start.py)

Flutter n'a pas pu être installé/compilé dans l'environnement où ce projet a été
généré — Flutter a besoin de télécharger son SDK Dart depuis les serveurs Google,
inaccessibles dans ce sandbox précis (testé : le clonage du SDK Flutter lui-même
depuis GitHub fonctionne, seul le téléchargement du binaire Dart échoue). En
attendant un éventuel portage Flutter (l'API est déjà conçue pour être consommée
par n'importe quel frontend), le même moteur est exposé via une API FastAPI qui
sert aussi directement le frontend web — un seul serveur, une seule URL.

```bash
cd iversen_engine
pip install -r requirements.txt
uvicorn app:app --port 8000
```

Puis ouvrir `http://localhost:8000` — le frontend et l'API sont servis ensemble
par la même commande (voir le `app.mount(...)` en toute fin de `app.py`). Un
bouton « 📷 Depuis une photo » permet de tester l'OCR directement depuis l'interface.

Testé dans ce sandbox : `/api/health`, `/api/correct` (9 types de fonctions, cas
valide et invalide), `/api/examples`, `/api/ocr` (image propre, image avec exposant
mal lu, image blanche/bruitée), `/api/ocr-page` (photo pleine page avec consigne +
exercice + question, ligne correcte classée en tête) — tous répondent correctement
(voir historique de la conversation pour les sorties brutes de `curl`).

## Recadrage automatique sur une photo pleine page

`/api/ocr-page` (bouton « 📄 Photo pleine page » dans le frontend) traite le cas où
la photo n'est pas déjà recadrée sur la seule ligne de l'exercice — une consigne
au-dessus, une question en dessous, etc. Le pipeline :
1. détecte toutes les lignes de texte via les boîtes englobantes de Tesseract
   (`pytesseract.image_to_data`)
2. calcule un score de vraisemberlance « ressemble à une expression mathématique »
   par ligne (proportion de caractères typiques d'une formule, bonus pour un `=`,
   malus pour une ligne longue et bavarde façon consigne)
3. renvoie les meilleures lignes classées, chacune déjà passée par le même
   nettoyage/parsing que le mode ligne unique

Validé sur une photo synthétique à 4 lignes (consigne + définition + fonction +
question) : la ligne contenant réellement `f(x) = 2x + 1` est classée en tête avec
un score de 1.0, loin devant les lignes de texte (score ≤ 0.2) — voir
`test_ocr_page_mode_ranks_the_exercise_line_first`. Le frontend affiche toujours les
candidats pour choix manuel, jamais de sélection automatique silencieuse.

## Résolution d'équations (nouveau module, même philosophie)

Deuxième type d'exercice couvert, en plus de l'étude de fonction : `engine/equations.py`
+ `engine/writer_equations.py`, endpoint `POST /api/solve-equation`.

- **Équations linéaires** (ax + b = 0) : isolement direct de x
- **Équations quadratiques** (ax² + bx + c = 0) : identification des coefficients,
  calcul du discriminant Δ, et les 3 cas classés séparément (Δ > 0 : deux solutions,
  Δ = 0 : solution double, Δ < 0 : aucune solution réelle — jamais présenté comme une
  erreur, mais comme un résultat mathématique correct)
- **Repli général** (degré ≥ 3, non polynomial) via résolution symbolique SymPy, avec
  un signalement explicite (`is_complete=False` + avertissement) quand SymPy ne garantit
  pas l'exhaustivité des solutions
- Chaque correction se termine par une **vérification par substitution** d'une solution
  trouvée dans l'équation normalisée, pour montrer qu'on retombe bien sur 0

Testé : les 3 cas de discriminant, une équation linéaire, une cubique, et la vérification
finale (`test_equation_correction_verification_step_checks_out`) — 7 tests dédiés.

## Résolution d'inéquations

Troisième type d'exercice, construit sur le même patron : `engine/inequalities.py` +
`engine/writer_inequalities.py`, endpoint `POST /api/solve-inequality`.

- **Linéaires** : isolement de x avec inversion explicite du sens de l'inégalité quand
  on divise par un coefficient négatif (erreur fréquente chez les élèves — signalée
  clairement dans la correction plutôt que juste appliquée silencieusement)
- **Quadratiques** : réutilise le calcul du discriminant d'`equations.py`, puis applique
  la règle du signe du trinôme (signe de a à l'extérieur des racines, signe opposé entre
  elles) pour les 3 cas de Δ
- **Décision de conception importante** : l'ensemble solution final n'est jamais
  recalculé « à la main » à partir du tableau de signes — il vient toujours de
  `sp.solveset()` (SymPy), l'implémentation la mieux testée disponible. Le tableau de
  signes n'est là que pour la pédagogie ; s'il y avait un désaccord entre le raisonnement
  pédagogique et SymPy, c'est SymPy qui doit gagner.

Testé : coefficient positif et négatif (linéaire), les 3 cas de discriminant (quadratique),
et le rejet propre d'une égalité passée par erreur à la place d'une inéquation — 7 tests dédiés.

## Systèmes de 2 équations linéaires (méthode de substitution)

Quatrième type d'exercice : `engine/systems.py` + `engine/writer_systems.py`,
endpoint `POST /api/solve-system`.

- Reconstruit la **méthode de substitution** enseignée au collège/lycée : isoler une
  inconnue dans la première équation, la substituer dans la seconde, résoudre, puis
  revenir en arrière pour l'autre inconnue
- Gère les 3 cas possibles pour un système 2×2 : **solution unique** (droites
  sécantes), **aucune solution** (droites strictement parallèles), **infinité de
  solutions** (droites confondues — présenté avec un paramètre libre `t`, pas un
  artefact du type « y = y »)
- Comme pour les inéquations, l'ensemble solution final vient toujours de
  `sp.linsolve()` (SymPy) ; la méthode de substitution reconstruite pas à pas sert
  uniquement à expliquer, jamais à recalculer le résultat définitif
- Validation d'entrée stricte : rejette une équation non linéaire (ex: `x**2 + y = 5`)
  ou sans signe `=`, avec un message d'erreur explicite plutôt qu'un plantage

Testé : les 3 cas de solution, la vérification finale par substitution dans les deux
équations d'origine, et le rejet des entrées invalides — 6 tests dédiés.

## Suites définies par récurrence

Cinquième type d'exercice : `engine/sequences.py` + `engine/writer_sequences.py`,
endpoint `POST /api/analyze-sequence`. Entrée : un premier terme et une récurrence
u_{n+1} = f(u_n) donnée comme expression en la variable `u` (ex : `"u + 3"` pour une
suite arithmétique, `"2*u + 3"` pour une arithmético-géométrique).

- **Classification automatique** par degré du polynôme f(u) : arithmétique (f(u)=u+r),
  géométrique (f(u)=q·u), arithmético-géométrique (f(u)=a·u+b), ou « non reconnue »
  si f n'est pas affine (ex: `u**2 - 1`) — dans ce dernier cas, le moteur calcule
  quand même quelques termes numériques mais annonce honnêtement qu'aucune formule
  fermée n'est trouvée automatiquement, plutôt que d'inventer une méthode
- **Suite arithmético-géométrique** : méthode du point fixe (L = b/(1-a), puis
  v_n = u_n - L est géométrique) reconstruite pas à pas — validée par un test qui
  recalcule la formule fermée contre les termes obtenus terme à terme et vérifie
  qu'ils coïncident exactement
- **Limite** couvrant tous les cas de raison (|q|<1, q=1, q>1, q≤-1 avec absence de
  limite par oscillation signalée comme telle, pas comme une erreur)

**Bug trouvé et corrigé pendant le développement** : le module utilisait involontairement
deux symboles SymPy `n` différents et incompatibles (l'un déclaré au niveau du module,
l'autre recréé localement dans la fonction) — un piège classique en SymPy où deux
symboles de même nom ne sont pas automatiquement égaux si leurs hypothèses diffèrent.
Le bug a été repéré par un test qui substituait explicitement une valeur dans la formule
fermée et comparait au terme numérique correspondant. Corrigé en unifiant sur un seul
symbole `n` exporté par le module.

Testé : arithmétique, géométrique (convergente/divergente/oscillante sans limite),
arithmético-géométrique (avec vérification numérique de la formule fermée), et le cas
non affine — 7 tests dédiés.

## Loi binomiale

Sixième type d'exercice : `engine/probability.py` + `engine/writer_probability.py`,
endpoint `POST /api/analyze-binomial`. Entrée : n (nombre d'épreuves), p (probabilité
de succès, fraction ou décimal), k optionnel (valeur ponctuelle demandée).

- Calcul **exact** (fractions SymPy, pas de flottants qui s'accumulent en erreurs) de
  P(X=k), P(X≤k), P(X≥k), E(X)=np, V(X)=np(1-p), σ(X)=√V(X)
- **Garde-fou intégré à la correction elle-même** : chaque correction se termine par
  la vérification que la somme de toute la distribution vaut 1 — si jamais un bug
  introduisait une erreur de calcul, ce serait immédiatement visible plutôt que silencieux
- Validation stricte des paramètres (p ∈ [0,1], 0 ≤ k ≤ n) avec messages d'erreur clairs

Testé : valeur connue de P(X=k), somme de la distribution égale à 1, cohérence entre
P(X≤k)+P(X≥k) et P(X=k) (le terme k est compté deux fois — identité vérifiée
explicitement plutôt que supposée), et le rejet de paramètres invalides — 7 tests dédiés.

## Nombres complexes

Septième type d'exercice, premier pas dans la Phase 3 du blueprint après les
probabilités : `engine/complex_numbers.py` + `engine/writer_complex.py`, endpoint
`POST /api/analyze-complex`.

- Forme algébrique, module, argument (avec détection des angles remarquables du
  cercle trigonométrique), formes trigonométrique et exponentielle, conjugué
- **Garde-fou intégré à la correction** (même principe que la loi binomiale) : chaque
  correction se termine par la vérification z × z̄ = |z|², qui rendrait immédiatement
  visible une erreur de calcul plutôt que de la laisser passer silencieusement
- Rejette proprement le cas dégénéré z=0 (argument non défini) et toute expression
  contenant une variable libre autre que i (ce module étudie un nombre complexe
  constant, pas une fonction de x)

Testé : angle remarquable vs non remarquable, les 4 quadrants du plan complexe, le
conjugué, et les deux cas de rejet (z=0, expression avec variable) — 7 tests dédiés.

## Calcul matriciel

Huitième type d'exercice : `engine/matrices.py` + `engine/writer_matrices.py`,
endpoints `POST /api/analyze-matrix` (une matrice : déterminant, trace, transposée,
inverse, rang) et `POST /api/matrix-operation` (deux matrices : somme, produit).

- Calcul exact (fractions SymPy) du déterminant, de la trace, de la transposée, de
  l'inverse (avec vérification systématique M×M⁻¹=I), et du rang
- Distingue proprement les cas où le déterminant/l'inverse n'ont pas de sens : matrice
  non carrée (déterminant non défini) ou déterminant nul (non inversible) — présentés
  comme des résultats mathématiques normaux, jamais comme des erreurs
- Validation stricte des dimensions pour les opérations à deux matrices (la somme exige
  des dimensions identiques, le produit exige que les dimensions internes coïncident),
  avec message d'erreur explicite indiquant précisément quelles dimensions posent problème
- Entrée simple côté frontend : notation `"1,2;3,4"` (lignes séparées par `;`,
  coefficients par `,`)

Testé : déterminant/inverse connus, matrice singulière, matrice non carrée, produit et
somme à résultat connu, rejet d'un produit à dimensions incompatibles, rejet d'une
matrice aux lignes de longueurs différentes, et vérification que M×M⁻¹-I redonne bien
la matrice nulle — 8 tests dédiés.

## Géométrie analytique

Neuvième type d'exercice, dernier grand chapitre mathématique du cahier des charges
initial : `engine/geometry.py` + `engine/writer_geometry.py`, endpoint
`POST /api/analyze-geometry`. Entrée : deux points A, B (obligatoires) et un
troisième point C optionnel.

- Avec A, B seuls : coordonnées du vecteur AB, distance AB, milieu de [AB], équation
  de la droite (AB) — avec gestion correcte du cas particulier d'une droite verticale
  (pas de coefficient directeur défini, testé explicitement)
- Avec C en plus : vecteur AC, test d'alignement des trois points par déterminant nul,
  test d'orthogonalité par produit scalaire nul — validé sur un triangle rectangle
  connu (orthogonalité détectée, non-alignement détecté) et sur trois points alignés
  connus
- Rejette proprement les points confondus (A=B, ou C=A) et les coordonnées malformées

Testé : distance/milieu/pente sur un cas connu, droite verticale, triangle rectangle,
points alignés, et les deux cas de rejet — 7 tests dédiés.

## Chimie — équilibrage d'équations (premier pas dans la Phase 4)

Dixième type d'exercice, et première brique de la Phase 4 du blueprint (Physique-Chimie) :
`engine/chemistry.py` + `engine/writer_chemistry.py`, endpoint `POST /api/balance-equation`.
C'était l'exemple explicitement cité dans le tout premier cahier des charges
(« Équilibrage automatique »).

- **Approche algébrique, pas du tâtonnement** : chaque équation de conservation
  (une par élément chimique) devient une ligne d'un système linéaire homogène ; les
  coefficients stœchiométriques s'obtiennent en cherchant le noyau (nullspace) de la
  matrice de composition via SymPy, puis en ramenant la solution aux plus petits
  entiers positifs (division par le PGCD)
- **Parseur de formules avec parenthèses imbriquées** (`Ca(OH)2`, `Al2(SO4)3`) — pas
  seulement des formules plates
- **Garde-fou intégré à la correction** (même principe que pour les probabilités et
  les nombres complexes) : chaque correction recompte explicitement chaque élément des
  deux côtés avec les coefficients trouvés et vérifie l'égalité — un test dédié
  (`test_chemistry_element_conservation_holds_for_all_coefficients`) vérifie cette
  cohérence indépendamment du format d'affichage, pour ne pas se contenter de comparer
  des chaînes de caractères

Testé : formation de l'eau, combustion du méthane, oxydation de l'aluminium (avec
composé à parenthèses), réduction de l'oxyde de fer, parsing de formules avec
parenthèses imbriquées, conservation vérifiée indépendamment pour chaque élément, et
rejet d'une équation sans flèche de réaction — 7 tests dédiés.

## Physique — circuits électriques

Onzième type d'exercice, deuxième brique de la Phase 4 : `engine/physics_circuits.py`
+ `engine/writer_physics_circuits.py`, endpoint `POST /api/analyze-circuit`. Résistances
en série ou en parallèle, loi d'Ohm, courant/tension/puissance de chaque composant.

- Calcul exact (fractions SymPy) : résistance équivalente, courant total, puis
  tension/courant/puissance individuels selon la topologie
- **Deux garde-fous de cohérence physique testés indépendamment** : en parallèle, la
  somme des courants de chaque branche doit être exactement égale au courant total
  (loi des nœuds) ; dans les deux topologies, la somme des puissances individuelles
  doit être exactement égale à la puissance totale — testés comme propriétés
  vérifiables, pas seulement affichés dans la correction
- Portée volontairement limitée à un seul type d'association à la fois (tout série ou
  tout parallèle) ; les réseaux mixtes demanderaient une analyse topologique plus
  générale, documentée comme hors périmètre de cette première itération plutôt que
  silencieusement mal gérée

Testé : valeurs connues en série et en parallèle, les deux garde-fous de cohérence
physique, et le rejet d'une résistance négative ou d'une topologie inconnue — 7 tests dédiés.

## Physique — cinématique (MRUV)

Douzième type d'exercice : `engine/physics_kinematics.py` + `engine/writer_physics_kinematics.py`,
endpoint `POST /api/analyze-kinematics`. Mouvement rectiligne uniformément varié : à
partir de x₀, v₀, a et t, calcule la position et la vitesse à l'instant t, et détecte
automatiquement les scénarios de freinage pour calculer le temps et la distance d'arrêt.

- Détection automatique de la décélération (a et v₀ de signes opposés) plutôt que de
  demander à l'utilisateur de préciser le type de scénario
- **Garde-fou physique testé sur plusieurs scénarios indépendants** : la relation
  v(t)² - v₀² = 2a(x(t)-x₀), qui ne fait pas intervenir t explicitement, doit toujours
  être vérifiée — testée séparément du calcul principal sur trois cas différents
  (freinage, accélération, chute libre), pas seulement affichée dans la correction

Testé : scénario de freinage complet (position, vitesse, temps et distance d'arrêt),
accélération depuis l'arrêt, la relation indépendante du temps sur 3 scénarios, et le
rejet d'un temps négatif — 5 tests dédiés.

## Physique — optique (lentille mince convergente)

Treizième type d'exercice, dernier grand pilier de physique du cahier des charges
initial : `engine/physics_optics.py` + `engine/writer_physics_optics.py`, endpoint
`POST /api/analyze-optics`. Relation de conjugaison de Descartes pour une lentille
mince convergente : position de l'image, grandissement, nature (réelle/virtuelle) et
orientation (droite/renversée).

- Validé sur les deux cas d'école classiques : objet éloigné → image réelle,
  renversée, réduite ; objet entre le foyer et la lentille → comportement de loupe
  (image virtuelle, agrandie, droite) — les deux vérifiés contre les valeurs exactes
  attendues, pas juste « ça ne plante pas »
- Rejette proprement les cas hors du périmètre assumé de ce module : lentille
  divergente (f' négatif), objet placé après la lentille (OA positif, physiquement
  incohérent avec la convention utilisée), et objet exactement au foyer objet (image
  à l'infini, pas de position finie)

Testé : les deux cas d'école (image réelle et loupe), et les trois cas de rejet
(lentille divergente, position d'objet positive, objet au foyer) — 6 tests dédiés.

## Chimie — stœchiométrie (complète la Phase 4 côté chimie)

Quatorzième type d'exercice : `engine/chemistry_stoichiometry.py` +
`engine/writer_stoichiometry.py`, endpoint `POST /api/analyze-stoichiometry`.
Réutilise directement l'équilibrage déjà construit (`engine/chemistry.py`) : à
partir d'une équation et d'une quantité connue (en grammes ou en moles) d'un seul
composé, calcule la quantité de matière et la masse de tous les autres.

- **Table de masses atomiques intégrée** (~45 éléments courants) pour calculer la
  masse molaire directement à partir de la formule, en réutilisant le même parseur
  de formules (avec parenthèses) que l'équilibrage
- **Garde-fou le plus rigoureux du projet sur ce module** : chaque correction
  vérifie explicitement la conservation de la masse totale (loi de Lavoisier :
  masse des réactifs = masse des produits) à la 6ᵉ décimale près, et ce calcul est
  re-vérifié indépendamment dans un test dédié — pas seulement affiché dans la
  correction générée

Testé : masses molaires connues (H₂O, CO₂), stœchiométrie exacte sur la combustion du
méthane (calcul en masse) et la formation de l'eau (calcul en moles direct), la
conservation de la masse totale vérifiée indépendamment, et le rejet d'un composé
absent de l'équation — 6 tests dédiés.

## Physique — thermodynamique (calorimétrie), Phase 4 complète

Quinzième et dernier type d'exercice de la Phase 4 : `engine/physics_thermodynamics.py`
+ `engine/writer_physics_thermodynamics.py`, endpoint `POST /api/analyze-thermodynamics`.
Deux modes : chaleur sensible (Q=mcΔT, changement de température) et chaleur latente
(Q=mL, changement d'état).

- Détermination automatique du sens du transfert thermique (chaleur reçue ou cédée)
  à partir du signe de Q, présentée comme une lecture physique du résultat plutôt
  qu'une simple valeur numérique
- Validé sur un cas de chauffage, un cas de refroidissement (Q négatif correctement
  identifié comme chaleur cédée) et un cas de changement d'état

Testé : chaleur sensible connue, refroidissement à Q négatif, chaleur latente connue,
et le rejet d'une masse négative — 5 tests dédiés.

**Avec ce module, la Phase 4 du blueprint est complète** : chimie (équilibrage +
stœchiométrie) et les quatre piliers de la physique lycée (électricité, cinématique,
optique, thermodynamique) sont tous couverts par un moteur dédié testé.

## Reconnaissance d'énoncé par photo (OCR) — Phase 2, première itération

Basée sur **Tesseract** (open-source, offline, aucun appel API). Installation :

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
pip install pytesseract Pillow python-multipart
```

**Portée honnête :** Tesseract est un OCR généraliste, **pas** un OCR mathématique
spécialisé (type Mathpix). Il lit correctement du texte imprimé net sur une seule ligne
(`f(x) = 2x + 1`), mais :
- confond fréquemment le caractère « ^ » (exposant) avec « * » (ou « 4 » selon la
  police) — testé et confirmé **structurel** : reproductible sur 2 polices différentes,
  à résolution ×1 et ×4, avec plusieurs modes de segmentation Tesseract (psm 6/7/8/11/13).
  Ce n'est pas un problème de réglage ; un vrai OCR mathématique (type Mathpix) demande
  un modèle entraîné spécifiquement sur des symboles mathématiques, hors de portée d'un
  OCR généraliste quelle que soit la configuration.
- ne gère pas les fractions empilées, les racines avec barre, les exposants réellement
  positionnés en exposant plutôt que tapés au clavier
- n'a **pas** été testé sur de l'écriture manuscrite dans cet environnement

C'est pourquoi `/api/ocr` ne renvoie **jamais** directement une correction : il renvoie
le texte brut ET une proposition nettoyée, que le frontend affiche pour confirmation/
édition obligatoire avant d'appeler `/api/correct`. Le pipeline de nettoyage
(`ocr/normalize.py`) tolère quand même pas mal de bruit : préfixes `f(x)=`/`y=`, opérateurs
unicode (×, ÷, −), exposants unicode (², ³), multiplication implicite (`2x(x-1)` →
`2*x*(x - 1)`), et rejette explicitement un texte qui ne contient aucune occurrence de x
(bruit OCR pur) plutôt que de produire un résultat absurde silencieusement.

Testé dans ce sandbox : image de texte imprimé propre sans exposant → extraction et
correction correctes de bout en bout (`test_ocr_pipeline_on_synthetic_image`) ; image
avec `^` → confirmé mal lu (« x^3 » lu « x*3 »), capturé et documenté plutôt que caché ;
image blanche/bruitée → rejet propre avec message actionnable plutôt qu'un résultat inventé.


## Couverture actuelle

- Ensemble de définition (polynômes, fractions rationnelles, exponentielle, logarithme, trigonométrie, valeur absolue, fonctions par morceaux)
- Parité (paire / impaire / non pertinente si le domaine n'est pas symétrique)
- Dérivée et dérivée seconde (y compris fonctions non lisses : Abs, Piecewise)
- Étude du signe de f' et tableau de variations, avec coupures forcées aux points anguleux
- Extremums locaux lisses (f'=0 avec changement de signe) **et** points anguleux
  (Abs, Piecewise) — classés séparément et étiquetés « dérivée non définie en ce point »
  quand c'est le cas, plutôt que présentés comme un f'=0 ordinaire
- Points d'inflexion (avec détection du changement de signe de f'', pas juste f''=0)
- Limites aux bornes réelles du domaine (plus de résultat aberrant type 1/0 pour log(x) en -∞)
- Asymptotes verticales, horizontales, obliques, avec formatage propre (« y = x - 2 »,
  pas « y = 1x + -2 ») ; les fonctions oscillantes comme sin/cos n'en génèrent plus à tort
- Fonctions périodiques (sin, cos, tan) : étudiées sur une fenêtre représentative bornée
  [-2π, 2π], explicitement annoncée dans la correction (pas de liste infinie de points)
- Notation pondérée par étape (dérivée et signe de f' pèsent plus que la parité, par
  exemple) — voir avertissement ci-dessous sur ce que ce score représente réellement
- Timeout de 10s par requête côté API, en défense en profondeur (voir `app.py`)

## Ce que mesure (et ne mesure pas) le score affiché

Le moteur génère ici la correction de **référence** (le corrigé), pas l'évaluation d'une
copie d'élève. Le score reflète la complétude du corrigé généré — proche de 20/20 par
construction — pas une performance d'élève. Comparer une réponse d'élève au corrigé
(avec pénalités pour méthode incomplète ou erreur de calcul) est prévu pour la Phase 2/3,
une fois l'entrée par photo/OCR en place et un vrai texte d'élève disponible à comparer.

## Bugs corrigés pendant cette itération (à noter pour la suite)

- **`tan(x)` bloquait le moteur indéfiniment.** Son domaine périodique est représenté en
  interne par SymPy comme un `Complement` (réels privés d'une union infinie de points).
  Le décomposeur de domaine ne le reconnaissait pas et retombait sur un intervalle non
  borné (-∞, ∞) — la recherche des zéros de f'' tentait alors d'itérer sur un ensemble de
  solutions périodiques infini. Corrigé en (1) reconnaissant explicitement les domaines
  `Complement`, (2) n'acceptant plus jamais qu'un `FiniteSet` explicite comme résultat de
  recherche de zéros. Test : `test_tan_does_not_hang_and_has_no_extrema`.
- **Points anguleux (`Abs`, `Piecewise`) non détectés au départ.** Un simple changement de
  pente sans passage par zéro de la dérivée (ex: `Piecewise((x**2, x<1), (2*x-1, True))`
  en x=1, pentes 2 puis 2 — continu mais pas toujours nul) n'était pas repéré. Ajout d'un
  détecteur de points de rupture structurels (zéros des arguments de `Abs`, bornes des
  conditions de `Piecewise`) injectés à la fois dans l'étude de signe et la recherche
  d'extremums, avec un étiquetage explicite « point anguleux ». Tests :
  `test_abs_function_detects_angular_minimum`, `test_piecewise_detects_corner_without_extremum`.

## Limites connues (honnêtes, à traiter en Phase 3)

- La parité n'est pas déterminée sur les domaines périodiques complexes (type `Complement`
  de tan) même quand elle existe réellement (tan est en fait impaire) — le moteur répond
  prudemment « non pertinente » plutôt que de risquer une conclusion fausse
- La détection de points anguleux dans `Piecewise` suppose des conditions simples de la
  forme `x < a` / `x >= a` ; des conditions composées (`(x >= 0) & (x < 5)`) ne sont pas
  encore extraites
- L'OCR (voir section dédiée ci-dessus) est fiable sur du texte imprimé propre sans
  exposant en caret ; pas encore d'écriture manuscrite, ni de fractions empilées
- Le score de vraisemblance du mode page complète est une heuristique simple
  (proportion de caractères typiques d'une formule) — testé et confirmé fonctionnel
  y compris sur une photo de cahier synthétique dégradée (voir section dédiée ci-dessous),
  mais jamais sur une vraie photo prise avec un téléphone
- Le timeout de requête API est une protection « molle » : le calcul SymPy en cours dans
  le thread continue en arrière-plan même après la réponse 422 (Python ne peut pas tuer un
  thread proprement) — suffisant pour ne jamais bloquer un utilisateur, mais à durcir
  (process séparé + kill) avant une mise en production

## Robustesse testée sur des photos de cahier dégradées (grille, éclairage, rotation, flou)

Le prétraitement initial (seuil global fixe) échouait complètement dès qu'un facteur de
dégradation réaliste était introduit. Plutôt que de deviner quoi corriger, chaque facteur
a été isolé et testé séparément sur une image synthétique :

| Facteur testé isolément | Résultat OCR |
|---|---|
| Aucune dégradation (référence) | ✅ `f(x) = 2x + 1` correct |
| Grille de cahier (lignes bleu clair) seule | ✅ toujours correct |
| Légère rotation (2,5°) seule | ✅ toujours correct |
| Flou léger seul | ✅ toujours correct |
| **Éclairage inégal (gradient) seul** | ❌ résultat illisible |
| Les 4 facteurs combinés | ❌ résultat illisible |

**L'éclairage inégal était donc, de loin, le vrai problème** — pas la grille ni la
rotation comme on aurait pu le supposer a priori. Le correctif apporté :
1. **suppression de grille par couleur** (les pixels bleu clair caractéristiques d'un
   papier quadrillé sont détectés et repeints en blanc, sans toucher au texte sombre)
2. **redressement automatique** (détection d'angle via le rectangle englobant minimal
   des pixels d'encre, rotation de correction)
3. **seuillage ADAPTATIF** plutôt que global fixe — c'est le changement qui corrige
   spécifiquement l'éclairage inégal, confirmé par un test isolé avant/après

Résultat sur l'image combinant les 4 facteurs de dégradation : le mode page complète
(`/api/ocr-page`) identifie correctement la ligne `f(x) = 2x + 1` avec un score de
vraisemblance de 0.89, malgré un artefact de bruit résiduel en tête de ligne (un « | »
parasite) — corrigé par un nettoyage additionnel des caractères de bruit en début de
ligne. Le pipeline complet (photo dégradée → OCR → nettoyage → expression correcte)
est verrouillé par `test_ocr_page_mode_survives_realistic_notebook_photo`.

**Ce qui n'est toujours pas testé** : une vraie photo prise avec un téléphone (bruit
de capteur, JPEG, ombres portées non linéaires, papier froissé) reste différente d'une
dégradation synthétique contrôlée. C'est l'écart restant le plus probable avec un usage réel.

## Export PDF et Word

Fonctionnalités explicitement demandées dans le cahier des charges initial et absentes
jusqu'ici : `export_engine/` + endpoints `POST /api/export-pdf` et `POST /api/export-docx`,
boutons « ⬇ Exporter en PDF » / « ⬇ Exporter en Word » sous chaque correction dans le frontend.

- **Générique sur les 6 types d'exercice** : les deux endpoints reçoivent le dict de
  correction déjà calculé par n'importe lequel des autres endpoints et le mettent en
  page — aucune logique spécifique par type d'exercice dans l'export lui-même
- **Même moteur de rendu de formules pour les deux formats** (`latex_render.py`,
  matplotlib mathtext) : une seule brique à maintenir plutôt que deux
- **Choix technique pour le Word** : `python-docx` plutôt que la bibliothèque Node
  recommandée par le skill docx de cet environnement — ce module fait partie d'un
  service backend Python redistribuable appelé depuis l'API (comme l'export PDF), pas
  d'une génération ponctuelle de document dans un environnement interactif ; rester
  100% Python évite d'ajouter une dépendance Node à l'ensemble du projet pour cette
  seule fonctionnalité
- Rendu mathématique réel dans les deux cas (fractions, exposants, racines, coefficients
  binomiaux), jamais du texte brut sauf échec avéré du rendu — voir le repli documenté
  dans `latex_render.py`
- Reprend l'identité visuelle de la maquette (encre bleu-nuit, rouge pour les
  avertissements, doré pour la note)

Testé : génération d'un fichier réel (pas un mock) pour chacun des 6 types d'exercice
et dans les deux formats, avec vérification par `pypdf` (PDF) et `python-docx` (Word)
que le fichier produit est valide et contient du texte + des images de formules ; le
DOCX généré a aussi été converti en PDF via LibreOffice puis en image pour inspection
visuelle directe pendant le développement. Un test dédié vérifie explicitement qu'aucune
formule ne retombe silencieusement sur le repli texte brut dégradé — un export qui
« marche » mais produit des formules illisibles serait pire qu'un échec franc.

## Tracé de courbes — complète la Phase 2 du blueprint

Jusqu'ici seule la moitié « reconnaissance » de la Phase 2 (OCR) était faite ; le
tracé de courbes — annoncé dans la toute première maquette du projet, bouton « Voir la
courbe » resté décoratif jusqu'à maintenant — est construit : `plot_engine/curve_plot.py`,
endpoint `POST /api/plot`, bouton « 📈 Voir la courbe » dans le frontend (uniquement
pour l'onglet Étude de fonction, seul type d'exercice qui a un vrai domaine numérique
à tracer).

- **Aucun second calcul** : le graphique réutilise directement `FunctionAnalysis`
  (extremums, points d'inflexion, asymptotes, domaine) déjà produit par
  `engine.functions.analyze()` pour annoter le tracé — un seul calcul, deux usages
  (correction rédigée + graphique)
- **Fenêtre d'affichage automatique** basée sur les points caractéristiques réels de
  la fonction plutôt qu'un intervalle fixe arbitraire
- **Gestion des asymptotes verticales** : les valeurs qui explosent numériquement
  près d'une asymptote sont découpées via un seuillage par percentile, pour éviter
  qu'un trait quasi-vertical unique n'écrase tout le graphique (cas testé explicitement
  sur une fraction rationnelle avec asymptote verticale)
- Esthétique cohérente avec le reste du projet (fond crème, grille bleu clair, encre
  bleu-nuit, extremums et points d'inflexion annotés avec leurs coordonnées)

Testé : contrôle **quantitatif** (écart-type des pixels d'image, pas juste « le fichier
existe ») qu'un vrai graphique est bien dessiné et non un canevas vide ; fonction
rationnelle avec asymptote verticale sans crash ; fonctions trigonométrique/logarithme/
valeur absolue sans crash ; fenêtre d'affichage qui englobe effectivement les points
caractéristiques calculés.

## Prochaine étape suggérée

Statut global : Phase 0 partielle (pas de vrai Flutter, SDK indisponible dans ce
sandbox), Phase 1 largement dépassée, Phase 2 complète (OCR + graphiques), Phase 3
fonctionnellement complète (probabilités, nombres complexes, calcul matriciel,
géométrie analytique), **Phase 4 complète** (chimie et les quatre piliers de la
physique lycée). Il ne reste que les Phases 5 (mode offline réel avec CAS natif et IA
embarquée) et 6 (niveau supérieur, polish, accessibilité) du blueprint initial.

Il reste un écart non résolu, déjà signalé plus haut : l'OCR n'a été testé que sur des
dégradations synthétiques, jamais une vraie photo de téléphone.
