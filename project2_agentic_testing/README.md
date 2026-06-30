# Projet 2 — Testing agentique (Selenium + DOM + OCR + Minikube)

Architecture du projet :

- `src/testing_agentic/generator.py` : création des cas de test JSON
- `src/testing_agentic/executors/api_executor.py` : appels HTTP vers l'API cible
- `src/testing_agentic/executors/web_executor.py` : exécution Web via Selenium et le DOM
- `src/testing_agentic/executors/mobile_executor.py` : exécution mobile (Appium, optionnel)
- `src/testing_agentic/ocr.py` : lecture d'images / screenshots avec OCR
- `src/testing_agentic/evaluator.py` : scoring et verdicts
- `src/testing_agentic/reporter.py` : rapport Markdown / CSV

Lancement local :

```powershell
pip install -r requirements.txt
python -m project2_agentic_testing.src.testing_agentic.orchestrator
```

Pré-requis :

- Selenium + navigateur + driver
- Tesseract si tu veux activer l'OCR
- Minikube si tu veux simuler un déploiement local Kubernetes
