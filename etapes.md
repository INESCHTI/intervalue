# Étapes de travail de A à Z

Ce fichier décrit le chemin complet à suivre pour construire le projet proprement, sans sauter d'étape.

## Phase 0 — Préparation

1. Vérifier que `Docker Desktop` est installé et démarré.
2. Vérifier que `Ollama` est installé et accessible.
3. Vérifier que Python fonctionne dans le workspace.
4. Préparer un environnement virtuel Python si nécessaire.
5. Décider si tu veux exécuter le Projet 1 uniquement en local ou aussi dans `Minikube`.

## Phase 1 — Cadrage

1. Relire les deux PDF pour extraire les besoins.
2. Identifier les tâches du Projet 1 : résumé, extraction, Q&A, classification.
3. Identifier les canaux du Projet 2 : API, Web, Mobile.
4. Définir les critères de succès : latence, qualité, format, robustesse, hallucinations.
5. Définir les formats de sortie : JSON, CSV, Markdown.

## Phase 2 — Construction du Projet 1

1. Créer le client `Ollama`.
2. Créer les schémas d'entrée/sortie.
3. Créer les templates de prompts.
4. Créer l'API `FastAPI`.
5. Ajouter un endpoint de santé.
6. Ajouter un endpoint principal `/nlp/process`.
7. Gérer les erreurs de connexion à Ollama.
8. Ajouter les tâches NLP une par une.
9. Ajouter le benchmark.
10. Ajouter le corpus de test.
11. Produire un premier rapport.

## Phase 3 — Déploiement du Projet 1

1. Tester l'application en local.
2. Créer un `Dockerfile`.
3. Builder l'image avec Docker Desktop.
4. Lancer le conteneur.
5. Si besoin, importer l'image dans `Minikube`.
6. Ajouter un `Deployment` et un `Service` Kubernetes.
7. Tester le service dans l'environnement local Kubernetes.

## Phase 4 — Construction du Projet 2

1. Créer le générateur de cas de test.
2. Définir la structure des cas JSON.
3. Créer l'exécuteur API.
4. Relier l'exécuteur API au Projet 1.
5. Créer l'exécuteur Web avec `Selenium`.
6. Choisir les bons sélecteurs sur le `DOM`.
7. Capturer des screenshots après les actions importantes.
8. Ajouter l'`OCR` pour lire les captures.
9. Créer l'évaluateur.
10. Créer le reporter.
11. Enchaîner le pipeline complet.

## Phase 5 — Tests de validation

1. Vérifier que le Projet 1 répond correctement.
2. Vérifier que le Projet 2 appelle bien le Projet 1.
3. Comparer les réponses entre API et Web.
4. Vérifier les cas limites : texte vide, message très court, erreur serveur.
5. Contrôler les résultats OCR sur screenshot.
6. Calculer les scores et les verdicts.

## Phase 6 — Benchmark et analyse

1. Lancer le benchmark sur plusieurs modèles.
2. Mesurer latence, tokens/s et qualité.
3. Comparer les résultats entre modèles.
4. Produire tableaux et graphiques.
5. Résumer les conclusions.

## Phase 7 — Industrialisation

1. Nettoyer l'arborescence.
2. Ajouter les tests unitaires.
3. Ajouter les tests d'intégration.
4. Automatiser le lancement des scripts.
5. Documenter les commandes utiles.
6. Préparer une version demo ou soutenance.

## Phase 8 — Livrable final

1. Un Projet 1 fonctionnel et documenté.
2. Un Projet 2 capable de tester le Projet 1.
3. Un corpus de test versionné.
4. Des rapports lisibles.
5. Une architecture claire et reproductible.

## Résumé du chemin global

Le chemin complet est :

1. comprendre
2. structurer
3. coder le Projet 1
4. déployer le Projet 1
5. coder le Projet 2
6. relier les deux
7. tester
8. mesurer
9. documenter
10. livrer
