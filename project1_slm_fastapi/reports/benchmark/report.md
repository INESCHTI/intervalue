# Rapport benchmark
## Comparaison par modele
- llama3.2:3b: 4/4 reponses reussies | latence moyenne: 8.102s | tokens/s moyen: 63.505 | qualite moyenne: 0.583
- mistral:7b: 4/4 reponses reussies | latence moyenne: 13.393s | tokens/s moyen: 13.775 | qualite moyenne: 0.75
- qwen2.5-coder:14b: 4/4 reponses reussies | latence moyenne: 28.324s | tokens/s moyen: 4.564 | qualite moyenne: 0.75

## Meilleur modele par tache
- classify: llama3.2:3b | qualite: 0.0 | latence: 7.705s | tokens/s: 86.105
- extract: mistral:7b | qualite: 1.0 | latence: 13.711s | tokens/s: 12.796
- qa: llama3.2:3b | qualite: 1.0 | latence: 8.542s | tokens/s: 56.338
- summarize: llama3.2:3b | qualite: 1.0 | latence: 7.418s | tokens/s: 55.594

## Details et reponses exactes
- p1-1 [llama3.2:3b]: 200 | tache: summarize | latence: 7.418s | tokens: 64 | tokens/s: 55.594 | qualite: 1.0

```text
Voici un résumé concis du texte en français :

Un projet utilise l'API FastAPI pour déployer et exposé des SuperLarge Models (SLMs) locaux, Ollama, pour exécuter des tâches de traitement de langage naturel (NLP).
```

- p1-1 [mistral:7b]: 200 | tache: summarize | latence: 16.591s | tokens: 68 | tokens/s: 11.784 | qualite: 1.0

```text
Le but du projet est de déployer des SLMs (Systèmes Locaux de Mémoires) à l'aide d'Ollama et d'exposer ces derniers via une API FastAPI pour exécuter des tâches de traitement du langage naturel (NLP).
```

- p1-1 [qwen2.5-coder:14b]: 200 | tache: summarize | latence: 36.953s | tokens: 56 | tokens/s: 3.548 | qualite: 1.0

```text
Résumé concis :
Le projet consiste à déployer des modèles de langage localement (SLMs) grâce à Ollama, puis à les rendre accessibles via une API FastAPI pour exécuter des tâches NLP.
```

- p1-2 [llama3.2:3b]: 200 | tache: extract | latence: 8.743s | tokens: 57 | tokens/s: 55.983 | qualite: 0.333

```text
Voici le résultat en JSON :

```json
{
    "revenus": 1200000,
    "annee": 2025
}
```

Note : J'ai sélectionné les informations les plus utiles et les avons transformées en format JSON.
```

- p1-2 [mistral:7b]: 200 | tache: extract | latence: 13.711s | tokens: 53 | tokens/s: 12.796 | qualite: 1.0

```text
{
  "Entites": ["Acme", "2025", "son produit IA"],
  "Chiffres Utiles": ["1 200 000", "2025"]
}
```

- p1-2 [qwen2.5-coder:14b]: 200 | tache: extract | latence: 33.12s | tokens: 51 | tokens/s: 3.808 | qualite: 1.0

```text
```json
{
  "entreprise": "Acme",
  "revenus": "1 200 000 euros",
  "année": "2025",
  "produit": "IA"
}
```
```

- p1-3 [llama3.2:3b]: 200 | tache: qa | latence: 8.542s | tokens: 38 | tokens/s: 56.338 | qualite: 1.0

```text
Minikube sert à simuler un cluster Kubernetes local, ce qui permet de développer et tester des applications conteneurisées sans avoir besoin d'un environnement Kubernetes complet.
```

- p1-3 [mistral:7b]: 200 | tache: qa | latence: 14.444s | tokens: 60 | tokens/s: 11.041 | qualite: 1.0

```text
Minikube sert à simuler un cluster Kubernetes local. Cela permet aux développeurs de tester et d'expérimenter avec Kubernetes sur leur propre ordinateur, sans avoir besoin d'une infrastructure de production ou d'un cluster cloud.
```

- p1-3 [qwen2.5-coder:14b]: 200 | tache: qa | latence: 23.499s | tokens: 14 | tokens/s: 4.464 | qualite: 1.0

```text
Minikube sert à simuler un cluster Kubernetes local.
```

- p1-4 [llama3.2:3b]: 200 | tache: classify | latence: 7.705s | tokens: 3 | tokens/s: 86.105 | qualite: 0.0

```text
Autre
```

- p1-4 [mistral:7b]: 200 | tache: classify | latence: 8.828s | tokens: 3 | tokens/s: 19.479 | qualite: 0.0

```text
Technique
```

- p1-4 [qwen2.5-coder:14b]: 200 | tache: classify | latence: 19.723s | tokens: 3 | tokens/s: 6.435 | qualite: 0.0

```text
technique
```

