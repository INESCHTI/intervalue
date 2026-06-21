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
python -m project1_slm_fastapi.src.slm_api.main
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
python -m project1_slm_fastapi.src.benchmark.runner
```

Le benchmark utilise `data/corpus/sample.json` et écrit un rapport dans `reports/benchmark/`.

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
