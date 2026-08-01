# Démarrer l'application — guide pas à pas (débutant)

Ce guide suppose que tu ne connais pas la ligne de commande. Suis les étapes dans l'ordre.

## Étape 1 — Installer Python (si ce n'est pas déjà fait)

Va sur **https://python.org/downloads** et installe la dernière version.

- **Windows** : pendant l'installation, coche bien la case *"Add Python to PATH"* en bas de la première fenêtre — c'est l'erreur la plus fréquente si ça ne marche pas ensuite.
- **Mac** : l'installateur standard suffit.

Pour vérifier que ça a marché, ouvre un terminal (voir étape 2) et tape :
```
python3 --version
```
Tu dois voir une version genre `Python 3.11.x`. Si tu es sur Windows et que `python3` ne marche pas, essaie juste `python --version`.

## Étape 2 — Ouvrir un terminal dans le dossier du projet

- **Windows** : ouvre le dossier du projet dans l'Explorateur de fichiers, clique dans la barre d'adresse en haut, tape `cmd`, appuie sur Entrée.
- **Mac** : ouvre le dossier dans le Finder, fais un clic droit dans le dossier en maintenant Ctrl, choisis *"Nouveau terminal au dossier"* (ou ouvre l'app Terminal et tape `cd ` suivi d'un glisser-déposer du dossier).
- **Linux** : clic droit dans le dossier → *"Ouvrir un terminal ici"*.

## Étape 3 — Lancer l'application

Dans le terminal qui s'est ouvert, tape exactement ceci et appuie sur Entrée :

```
python3 start.py
```

(Sur Windows, si ça ne marche pas, essaie `python start.py`.)

**La première fois**, ça va prendre 1 à 2 minutes : le script installe tout ce qu'il faut tout seul. Tu vas voir défiler du texte avec des ✓ verts. C'est normal, laisse-le travailler.

À la fin, ton navigateur va s'ouvrir automatiquement sur l'application. Si ça ne s'ouvre pas tout seul, ouvre ton navigateur et tape dans la barre d'adresse :
```
http://localhost:8000
```

## Étape 4 — Utiliser l'application

Choisis un onglet (Étude de fonction, Équation, etc.), tape ou clique sur un exemple, clique sur le bouton pour lancer le calcul.

## Pour arrêter l'application

Retourne dans le terminal où tu as lancé `python3 start.py`, et appuie sur `Ctrl+C`. Tu peux aussi juste fermer la fenêtre du terminal.

## Pour la relancer plus tard

Refais juste l'étape 3 (`python3 start.py`) — ce sera beaucoup plus rapide la deuxième fois, tout est déjà installé.

## Si quelque chose ne marche pas

- **"python3 : commande introuvable"** → Python n'est pas installé ou pas dans le PATH. Retourne à l'étape 1.
- **Le texte parle de "Tesseract" manquant** → ce n'est pas grave, tout marche sauf la lecture de photos. Le script te donne la commande exacte pour l'installer si tu veux cette fonctionnalité.
- **Le port 8000 est déjà utilisé** → une ancienne copie du serveur tourne encore quelque part. Ferme tous les terminaux liés au projet, puis relance.
- **Autre problème** → copie le message d'erreur affiché dans le terminal, c'est la première chose à regarder pour comprendre ce qui bloque.
