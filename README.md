# Workspace `value`

Ce workspace contient deux projets distincts mais liés.

## Projet 1
`project1_slm_fastapi`

- expose des SLMs locaux via `Ollama`
- fournit une API `FastAPI`
- sert au benchmark des modèles
- peut être conteneurisé avec `Docker Desktop`
- peut être simulé en local avec `Minikube`

## Projet 2
`project2_agentic_testing`

- teste un agent conversationnel de manière autonome
- exécute des cas sur API, Web et Mobile
- utilise `Selenium` et le `DOM` pour le Web
- utilise l'`OCR` pour lire les screenshots
- peut consommer directement l'API du Projet 1

## Fichiers principaux

- `architecture.md` : explication détaillée des deux architectures
- `etapes.md` : plan complet de travail de A à Z
- `projets_details.md` : document de synthèse et contexte

## Démarrage rapide

```powershell
# Projet 1
pip install -r project1_slm_fastapi/requirements.txt
python -m project1_slm_fastapi.src.slm_api.main

# Projet 2
pip install -r project2_agentic_testing/requirements.txt
python -m project2_agentic_testing.src.testing_agentic.orchestrator
```

## Relation entre les projets

Le Projet 2 peut servir à tester l'API du Projet 1. Le premier produit le service, le second valide la qualité, les régressions et les écarts entre les canaux.

