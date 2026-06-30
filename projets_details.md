# Détails des deux projets, transcription de l'image et architectures

Ce document décrit en détail :
- le Projet 1 (SLMs locaux + FastAPI + benchmark)
- le Projet 2 (Testing agentique)
- le contenu interprété du tableau photo (`tableau.jpg`)

Tu m'as indiqué que tu utiliseras : Selenium, manipulation du DOM, Minikube, OCR. Tu as aussi Docker Desktop et Ollama installés — j'en tiens compte dans les architectures.

---

**Sommaire**

1. Projet 1 — Objectif et composants
2. Projet 1 — Architecture détaillée (composants + fichiers)
3. Projet 2 — Objectif et composants
4. Projet 2 — Architecture détaillée (composants + fichiers)
5. Rôle de Selenium / DOM / Minikube / OCR dans les deux projets
6. Transcription et interprétation du tableau (`tableau.jpg`)
7. Déploiement et commandes rapides (Docker / Ollama / Minikube)
8. Prochaines étapes recommandées

---

## 1. Projet 1 — Objectif et composants

Nom : "SLMs locaux + FastAPI + Benchmark"

But principal : déployer et exposer des Small Language Models (SLMs) en local via `Ollama`, fournir une API HTTP (FastAPI) pour exécuter des tâches NLP (résumé, extraction, Q&A, classification) et construire un module de benchmark reproductible pour comparer modèles sur métriques objectives (latence, tokens/s, RAM, qualité humaine, cohérence JSON, taux d'hallucination).

Composants fonctionnels :
- Gestion des modèles : `Ollama` (pull, run, serve localement)
- API applicative : `FastAPI` (endpoints par tâche NLP, streaming possible)
- Client Ollama : wrapper HTTP local pour appeler Ollama
- Prompts centralisés : templates (few-shot, rôles, format JSON)
- Corpus de test : jeux de données versionnés (JSON)
- Runner de benchmark : exécutions multi-modèles, collecte métriques
- Analyse & reporting : export CSV, graphiques PNG, rapports Markdown/HTML
- CI / tests : tests unitaires et d'intégration

Technos recommandées : Python 3.10+, FastAPI, uvicorn, httpx/requests, pandas, matplotlib/plotly, Ollama (installé), Docker pour packaging, Minikube pour exécution locale dans K8s si besoin pour réplication de production.

Sécurité & données : garder les données sensibles locales (pas d'upload), parametrer Ollama pour usage privé.

## 2. Projet 1 — Architecture détaillée

But : architecture modulaire, testable et réutilisable.

Architecture logique (composants) :

- Client utilisateur → API FastAPI (`/nlp/process`, `/nlp/stream`, endpoints par tâche)
- FastAPI → `Ollama` (HTTP local : ex. `http://localhost:11434`)
- Benchmark runner (process batch) appelle API localement ou appelle `Ollama` directement
- Stockage : `data/corpus/`, `reports/benchmark/`, `outputs/` pour CSV/PNG

Arborescence de fichiers conseillée (Projet 1 seul)

```
project_slm_fastapi/
├── docs/
│   └── design.md
├── src/
│   ├── api/
│   │   ├── main.py           # FastAPI app
│   │   ├── routes.py         # endpoints par tâche
│   │   └── streaming.py      # streaming SSE si necessaire
│   ├── clients/
│   │   └── ollama_client.py  # wrapper pour appels Ollama
│   ├── prompts/
│   │   └── templates.json    # prompts centraux
│   ├── tasks/
│   │   ├── summarize.py
│   │   ├── extract.py
│   │   └── qa.py
│   └── utils/
│       └── metrics.py        # calcul metriques benchmark
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   ├── corpus/
│   └── references/
├── reports/
│   └── benchmark/
├── Dockerfile
├── k8s/
│   └── deployment.yaml      # (optionnel) pour Minikube
└── README.md
```

Détails des composants :
- `ollama_client.py` : fonctions `generate(model, prompt, stream=False)`; gère retries, timeouts, et parsing JSON strict.
- `routes.py` : endpoints REST validés par Pydantic, chaque tâche mappe au template de prompt et appelle `clients.ollama_client`.
- `tasks/` : code pour post-traiter les réponses (parse JSON, vérifier format, calculer score de cohérence JSON).
- `metrics.py` : token count, latence, tokens/sec, RAM (si possible via /proc ou outils système), qualité humaine (export CSV pour annotation humaine).

Intégration Docker & Minikube :
- Dockerfile pour builder une image `project_slm_fastapi:latest` incluant dépendances et script de démarrage `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`.
- Déployer dans Minikube si tu veux simuler production : créer un `Deployment` et `Service` exposant le port 8000.
- Ollama peut rester en local (process sur la machine) ou être contenu dans un conteneur séparé si tu préfères (vérifier compatibilité et accès GPU si nécessaire).

Notes pratiques quand Ollama est installé localement :
- Vérifie `ollama list` et `ollama pull <model>` pour télécharger les modèles.
- Si Ollama écoute sur `11434`, configure `OLLAMA_URL` dans `ollama_client.py`.

## 3. Projet 2 — Objectif et composants

Nom : "Testing agentique" (Swarm-like agents)

But principal : construire un pipeline autonome (Generator → Executor → Evaluator → Reporter) pour tester un agent conversationnel sur plusieurs canaux : API, Web (navigateur), Mobile (optionnel), en automatisant génération de cas, exécution et évaluation automatique.

Composants fonctionnels :
- Generator : lit une spécification et génère cas de test (JSON)
- Executor : exécute cas via canaux (API, Web via Selenium, Mobile via Appium si besoin)
- Evaluator : compare actual vs expected, détecte hallucinations, calcule scores (pertinence, exactitude, format)
- Reporter : consolide résultats, produit Markdown/CSV et graphiques
- Orchestrateur / Swarm : gère handoffs et files d'exécution

Technos recommandées : Python, Selenium (Web), httpx/requests (API), Appium (Mobile) si nécessaire, OCR (Tesseract via pytesseract) pour lire textes dans screenshots, Docker/Minikube pour orchestrer environnements.

## 4. Projet 2 — Architecture détaillée

Architecture logique (composants) :

- Input : `test_spec.json` ou `corpus/` → Generator → produce list `test_cases.json`
- Executor : pour chaque test case, choisis canal :
  - API : POST/GET vers endpoint du chatbot
  - Web : Selenium automatisation (manipulation DOM, capture screenshot)
  - Mobile : Appium script
- Evaluator : prend return (text, screenshot), applique règles (parse JSON, NLI ou heuristiques) et renvoie score + verdict
- Reporter : agrège et génère `reports/testing/` (CSV, Markdown, dashboards)

Arborescence de fichiers conseillée (Projet 2 seul)

```
project_agentic_testing/
├── src/
│   ├── generator.py       # gen cases
│   ├── executor/
│   │   ├── api_executor.py
│   │   ├── web_executor.py    # Selenium
│   │   └── mobile_executor.py # Appium (optionnel)
│   ├── evaluator.py
│   └── reporter.py
├── tests/
├── data/
│   └── test_cases/
├── reports/
└── README.md
```

Détails techniques importants pour Selenium + DOM :
- Selenium contrôle un navigateur (chromedriver/edge/geckodriver). Le test code-based génère des actions sur le DOM (find_element, click, fill, wait_for).
- Utilise des sélecteurs stables (id, data-test) pour réduire la fragilité.
- Capture screenshot après chaque action clé et applique OCR (Tesseract) si tu veux vérifier le texte visuel.
- Pour des tests répétés, containeriser le runner Selenium (ou utiliser Playwright) et exécuter dans Minikube si tu veux paralléliser.

## 5. Rôle de Selenium / DOM / Minikube / OCR

- Selenium : exécution des tests côté Web. Utile pour simuler interactions utilisateur (cliquer, taper, naviguer). Le `Executor` web utilisera Selenium pour produire `actual` et screenshots.

- DOM : Document Object Model — Selenium manipule directement le DOM de la page pour accéder aux éléments (textes, boutons). Le test doit se baser sur le DOM pour assertions structurelles (ex. élément `.bot-message:last-child`).

- OCR : extraction automatique de texte à partir d'images/screenshots. Utilise `pytesseract` pour valider visuellement le rendu (par ex. pour vérifier qu'une image contient un certain texte), détecter cas d'affichage erroné ou valeurs chiffrées visibles seulement en screenshot.

- Minikube : simuler un cluster Kubernetes local pour déployer l'API FastAPI et/ou le runner d'exécution dans des pods. Avantages : tester orchestration, scalabilité et comportement réseau; utile pour CI ou tests d'intégration proches de la prod.

Comment ces outils se complètent :
- Le `Executor` Web exécute Selenium → screenshot → OCR (vérification visuelle) → envoie résultat à `Evaluator`.
- L'API est déployée soit localement (uvicorn) soit dans un pod Minikube pour simuler environnement produit.

## 6. Contenu de l'image `tableau.jpg` (transcription et interprétation)

Observations principales :
- Le tableau contient une carte mentale liant : gouvernance (AI Act, RGPD), architecture agentique (fleet d'agents, agentic mesh), canaux (call bot, voice-to-text, TTS), formats (JSON, API, DOM), et usages métiers (fintech, customer support, pharma probable).
- Mots et concepts repérés (non exhaustif / manuscrit, lecture approximative) : `AI Act`, `RGPD`, `Fleet d'agents`, `Agentic Mesh`, `Call bot`, `STT/TTS`, `RAG`, `LLM`, `prompt`, `metrics`, `security`, `SDLC`.

Interprétation :
- Le tableau est un plan de gouvernance + architecture : relier conformité, couche modèle, orchestration agentique, et canaux d'interface utilisateur.
- Il insiste sur deux axes : conformité (AI Act / RGPD) et engineering (déploiement, monitoring, metrics).

Utilisation pratique :
- Ce tableau est parfait comme checklist architecturale avant implémentation : sécurité, logging, monitoring, formats d'API, et choix d'outils.

## 7. Déploiement et commandes rapides

Pré-requis : Docker Desktop installé (tu l'as) et Ollama installé localement (tu l'as). Minikube installé si tu veux simuler k8s.

Démarrage Ollama (exemple) :
```powershell
ollama pull mistral
ollama run mistral
# ou l'API locale si Ollama expose une API (suivant la version)
```

Lancer l'API FastAPI en local (exemple) :
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

Construire une image Docker (Projet 1) :
```powershell
docker build -t project_slm_fastapi:latest .
# pour Minikube
minikube image load project_slm_fastapi:latest
kubectl apply -f k8s/deployment.yaml
```

Exécution Selenium (local) :
- Installer `chromedriver` compatible avec ta version de Chrome ou utiliser `selenium-manager`.
- Script exemple (Python) :
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get('http://localhost:3000/chat')
input_el = driver.find_element(By.CSS_SELECTOR, '#chat-input')
input_el.send_keys('Bonjour')
# etc.
```

OCR (Tesseract) :
- Installer Tesseract (externe) et `pytesseract` dans l'environnement Python.

## 8. Prochaines étapes recommandées

1. Confirme si tu veux que je génère les structures de dossiers fisques pour les deux projets ou seulement pour l'un.
2. Je peux générer un `README.md` individuel et des squelettes de code (FastAPI minimal, Executor Selenium minimal).
3. Si tu veux intégration k8s, je peux fournir un `Dockerfile` et un `k8s/deployment.yaml` minimal.

---

Si tu veux, je crée maintenant les fichiers squelettes (un seul ou les deux). Dis lequel et je le génère. Je peux aussi préparer un petit script d'intégration qui démarre Ollama (si tu veux), l'API et exécute un cas de test Selenium + OCR.
