# Iversen Scientific

Application de correction automatique d'exercices scolaires (maths,
physique, chimie) — FastAPI + frontend HTML/JS, moteur symbolique SymPy,
OCR, export PDF/Word, graphiques interactifs, historique local.

## Démarrer en local

Voir [`iversen_engine/GUIDE_DEMARRAGE.md`](iversen_engine/GUIDE_DEMARRAGE.md)
(pas à pas, pensé pour un débutant) ou en résumé :

```bash
cd iversen_engine
python3 start.py
```

## Documentation complète

- [`iversen_engine/README.md`](iversen_engine/README.md) — vue d'ensemble du
  projet, architecture, modules
- [`iversen_engine/GUIDE_INSTALLATION_ET_COMPILATION.txt`](iversen_engine/GUIDE_INSTALLATION_ET_COMPILATION.txt) —
  installer les dépendances, puis compiler en `.exe` (Windows), `.dmg`
  (macOS) et `.apk` (Android)
- [`iversen_engine/native_cas/README.md`](iversen_engine/native_cas/README.md) —
  moteur de calcul symbolique natif en Rust (sous-projet indépendant)

## Compilation automatique (GitHub Actions)

Ce dépôt inclut un workflow (`.github/workflows/build.yml`) qui compile les
trois cibles sur les machines gratuites de GitHub, sans rien installer en
local : onglet **Actions** → *Build all targets* → *Run workflow*. Les
fichiers compilés apparaissent ensuite en téléchargement dans la section
*Artifacts* du run.

La tâche Android reste inactive tant que `iversen_mobile/` ne contient pas
encore de vrai projet Flutter (voir `iversen_mobile/README.md`).

## Tests

```bash
cd iversen_engine
pip install -r requirements.txt
pytest test_engine.py -v
```
