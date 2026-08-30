# OCR — disponibilité selon la plateforme

Ce module utilise **Tesseract** via `pytesseract`, plus OpenCV (`cv2`) pour le
prétraitement d'image (redressement, suppression de grille, seuillage
adaptatif — voir `reader.py`).

## Desktop / web (`iversen_engine/`, `run_desktop.py`)

Fonctionne normalement : `pip install -r requirements.txt` installe
`opencv-python-headless` et `pytesseract`, et il suffit d'avoir le binaire
`tesseract` installé sur la machine (le script `start.py` vérifie sa présence
et guide l'installation si besoin).

## Mobile Android (`iversen_mobile/android/.../python/`, via Chaquopy)

**L'OCR n'y est PAS disponible aujourd'hui**, et c'est voulu dans ce build :

- `pytesseract` a besoin d'exécuter le binaire `tesseract` en sous-processus.
  Une app Android sandboxée ne peut pas appeler un exécutable arbitraire non
  embarqué dans son propre paquet — il n'y a pas de wheel pip qui résout ce
  problème, contrairement à une dépendance purement Python.
- `cv2` (OpenCV) et `pytesseract` ne sont donc **volontairement pas** dans la
  liste `pip { install(...) }` de `android/app/build.gradle.kts`.
- Côté Python, `ocr/reader.py` importe ces deux paquets de façon défensive
  (`try/except ImportError`, drapeau `OCR_AVAILABLE`) : leur absence ne fait
  plus planter tout `app.py` au démarrage (c'était le cas avant correction —
  toute l'app, pas seulement l'OCR, était inutilisable sur Android). Les
  endpoints `/api/ocr` et `/api/ocr-page` renvoient maintenant une réponse
  HTTP 503 claire, et le frontend (`frontend/index.html`, via `/api/health`)
  masque le bouton photo et affiche un message explicite à la place.

### Piste retenue pour une vraie OCR mobile : Google ML Kit

`android/app/build.gradle.kts` déclare déjà la dépendance
`com.google.mlkit:text-recognition` — c'est la piste prévue pour un OCR natif
Android (rapide, pas de binaire externe, fonctionne hors-ligne). **Le pont
Python ↔ Java (Chaquopy `from java import ...`) reste à écrire** : appeler
`TextRecognition` côté Kotlin/Java depuis `ocr/reader.py` (ou exposer une
fonction équivalente à `extract_text()`/`extract_line_candidates()` avec la
même signature, pour que `app.py` n'ait rien à changer). Tant que ce pont
n'existe pas, l'OCR mobile reste indisponible — c'est un point identifié, pas
un oubli silencieux.
