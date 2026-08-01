# native_cas — moteur de calcul symbolique natif (Rust)

Première brique de la Phase 5 du projet (mode hors-ligne réel). Contrairement au
reste de l'application (Python), ce dossier contient un vrai programme Rust qui
se compile en un fichier exécutable autonome, sans dépendance à installer.

**Statut : v1 terminée.** Ce dossier a suivi un plan en 5 étapes, maintenant
toutes faites. Sauf demande explicite d'un nouveau projet, aucune nouvelle
fonctionnalité mathématique n'est ajoutée ici après cette version — voir
"Ce qu'il ne sait pas faire" ci-dessous, qui est une limite assumée, pas un
oubli.

## Ce qu'il sait faire aujourd'hui

- Lire un texte comme `x^3 - 3*x + 2` ou `sin(2*x) / (1 + x)` (nombres, x,
  +, -, *, / , ^ avec exposant entier, parenthèses, et les fonctions sin,
  cos, exp, ln)
- Calculer sa dérivée (règles de la somme, du produit, du quotient, de la
  puissance, de la chaîne)
- Afficher le résultat proprement, avec les parenthèses nécessaires pour que
  le texte affiché reste mathématiquement correct (ex: `(x + 1)^2`, pas
  `x + 1^2`)
- Refuser clairement, avec un message en français, les cas mathématiquement
  indéfinis qu'on peut détecter à l'avance : division par une expression qui
  vaut zéro (ex: `1/0`, ou `3/(2-2)` qui se simplifie en zéro), et `ln` d'un
  nombre négatif ou nul écrit en dur (ex: `ln(-3)`)

## Ce qu'il ne sait pas faire (limite assumée, pas un oubli)

- Les racines (`sqrt`), tan, les fonctions trigonométriques réciproques, et
  toute fonction en dehors de sin/cos/exp/ln
- Les exposants non entiers (`x^0.5`) — rejeté avec un message clair plutôt
  que de donner un résultat faux
- Prévoir qu'un `1/x` posera problème *seulement* si on l'évalue plus tard en
  x=0 : ça, seule l'évaluation numérique au moment voulu peut le savoir. Dans
  ce cas précis (pas une division littérale par zéro écrite dans le texte),
  le calcul suit la convention standard IEEE-754 : un flottant non-nul divisé
  par zéro donne l'infini, plutôt que de planter silencieusement. Ce
  comportement est intentionnel et verrouillé par un test
  (`evaluating_one_over_x_at_zero_follows_ieee754_convention_not_a_crash`).
- Une interface graphique — pour l'instant, uniquement en ligne de commande
- Une intégration avec l'application Python principale — ce sont deux
  sous-projets séparés pour l'instant

## Installer Rust (une seule fois)

```bash
sudo apt-get install rustc cargo   # Ubuntu/Debian
# ou : https://rustup.rs (toutes plateformes)
```

## Lancer

```bash
cd native_cas
cargo run -- "sin(2*x) / (1 + x)"
```

Sans argument, utilise l'exemple par défaut (`x^3 - 3*x + 2`).

## Lancer les tests

```bash
cargo test
```

30 tests : dérivées connues (somme, produit, quotient, chaîne, sin, cos, exp,
ln), lecture de texte avec parenthèses et signe moins, cas limites
(division par zéro littérale ou simplifiée, ln d'un nombre négatif ou nul),
et deux tests de non-régression sur de vrais bugs trouvés et corrigés
pendant le développement :
- le signe négatif du tout premier terme d'une somme disparaissait à
  l'affichage (`leading_negative_term_keeps_its_sign_in_display`)
- une somme utilisée comme base d'une puissance ou comme facteur d'un
  produit s'affichait sans les parenthèses nécessaires, ex. `(x+1)^2`
  affiché `x + 1^2` (`power_of_a_sum_keeps_parentheses_in_display`,
  `product_of_a_sum_keeps_parentheses_in_display`)

Dans les deux cas, le calcul lui-même était toujours correct ; seul le texte
affiché était trompeur.

## Fabriquer le fichier exécutable autonome

```bash
cargo build --release
./target/release/iversen_cas "x^4 - 2*x^2 + 1"
```

Le fichier `target/release/iversen_cas` (~13 Mo) peut être copié tel quel sur
n'importe quelle machine Linux compatible et lancé directement — aucune
installation requise, contrairement à la partie Python du projet.

## Fichiers

- `src/expr.rs` — représentation d'une expression, règles de dérivation, et
  la validation des cas indéfinis connus à l'avance
- `src/parser.rs` — transforme un texte en expression
- `src/main.rs` — point d'entrée en ligne de commande

## Et après ?

Rien n'est prévu ni promis au-delà de cette version : pas d'interface
graphique, pas de nouvelles fonctions mathématiques, pas de tentative
Flutter (bloquée dans ce sandbox — voir le README principal du projet). Si
tu veux repartir sur l'un de ces sujets, il faudra le redemander
explicitement dans une nouvelle discussion.

