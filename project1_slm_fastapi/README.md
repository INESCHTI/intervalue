# Projet 1 — SLMs locaux + FastAPI + Benchmark

Ce projet est exécutable de bout en bout avec Ollama local.

## Ce qu'il contient

- `src/slm_api/` : API FastAPI, schémas, prompts, client Ollama
- `src/benchmark/` : runner de benchmark, calcul de métriques, rapport
- `data/corpus/` : corpus de test JSON
- `reports/benchmark/` : sorties Markdown du benchmark
- `k8s/` : manifeste pour Minikube / Kubernetes
- `tests/` : tests unitaires et API

## Pré-requis

- Python 3.10+
- `Ollama` installé et lancé localement
- `Docker Desktop` si tu veux builder l'image
- `Minikube` si tu veux déployer localement dans Kubernetes

## Installation

```powershell
cd project1_slm_fastapi
pip install -r requirements.txt
```

## Lancement de l'API

```powershell
python run_api.py
```

Si tu veux lancer depuis la racine du workspace, tu peux aussi faire :

```powershell
cd d:\4DS\value\project1_slm_fastapi
python run_api.py
```

L'API expose :

- `GET /health`
- `POST /nlp/process`

## Test rapide sans Ollama

```powershell
pytest
```

Les tests API peuvent utiliser un mock pour valider le flux sans serveur Ollama actif.

## Démarrage du benchmark

```powershell
python run_benchmark.py
```

Le benchmark utilise `data/corpus/sample.json` et écrit un rapport dans `reports/benchmark/`.

Le rapport affiche maintenant :

- la latence de chaque modele
- les tokens/seconde quand Ollama fournit la metrique
- un score qualite base sur les mots-cles attendus du corpus
- le meilleur modele par tache
- le contenu exact des reponses

Le benchmark compare par défaut 3 modèles sur le même corpus :

- `llama3.2:3b` : petit modèle pour la vitesse
- `mistral:7b` : modèle moyen pour la qualité
- `qwen2.5-coder:14b` : modèle spécialisé code / raisonnement technique

Si un modèle n'est pas encore présent dans Ollama, il faut d'abord le récupérer avec `ollama pull`.

## Docker

```powershell
docker build -t project1_slm_fastapi:latest .
```

## Minikube

```powershell
minikube start
minikube image load project1_slm_fastapi:latest
kubectl apply -f k8s/deployment.yaml
```

## Ollama local

Avant de lancer l'API, ouvre Ollama localement et vérifie qu'il répond sur `http://localhost:11434`.

```powershell
ollama list
ollama pull mistral
```
