# Compte rendu complet des documents

Ce fichier rassemble le contenu des deux PDF du workspace et une transcription/interpretation du tableau photo `tableau.jpg`.

## 1. Projet SLMs - Explorer les Small Language Models

### Objectif general
Le projet presente comment exploiter des Small Language Models (SLMs) en local, puis les exposer via une API FastAPI et les comparer avec un benchmark objectif.

### Contexte et motivation
- Les LLMs usuels comme ChatGPT, Gemini, Claude ou Copilot sont heberges dans le cloud.
- Le projet veut explorer des SLMs qui tournent localement sur machine personnelle.
- Les avantages mis en avant sont :
  - pas de frais API
  - donnees privees
  - faible latence
  - personnalisation

### Difference LLM vs SLM
- LLMs : plusieurs dizaines de milliards de parametres, besoin de GPU puissants, acces payant via API, tres generaux.
- SLMs : quelques milliards de parametres, utilisables sur un laptop avec 8 a 16 Go de RAM, gratuits et open source, plus specialises.
- Exemples cites : Mistral 7B, LLaMA 3, Phi-3, Gemma.

### Architecture du projet
Le projet est presente en deux grandes parties :
- Backend IA avec FastAPI et Ollama.
- Benchmark et evaluation des SLMs.

### Partie 1 - Backend IA avec FastAPI
Points clefs :
- installer Ollama et telecharger des SLMs
- creer une API REST avec FastAPI
- implementer des taches NLP : extraction, resume, Q&A, etc.
- gerer le streaming des reponses
- tester via Swagger UI

### Partie 2 - Benchmark des SLMs
L'objectif est de :
- definir des metriques d'evaluation
- comparer vitesse, qualite et consommation memoire
- tester plusieurs modeles sur les memes taches
- produire des tableaux et graphiques
- identifier le meilleur modele selon l'usage

### Ollama
- Ollama est un outil open source pour faire tourner des SLMs localement.
- Il installe les modeles, expose une API REST locale sur le port 11434 et fonctionne sur Windows, Mac et Linux.
- Commandes de base : pull, run, list.

### Choix des modeles
Le document recommande de tester 3 modeles de tailles differentes :
- un petit modele pour la vitesse
- un modele moyen pour la qualite
- un modele specialise pour une tache particuliere

### Appel API Ollama
Le projet montre un appel Python vers `http://localhost:11434/api/generate` avec :
- mesure du temps d'execution
- nombre de tokens
- calcul des tokens par seconde
- latence en secondes

### Pourquoi FastAPI
Avantages mis en avant :
- Swagger UI genere automatiquement
- validation des donnees avec Pydantic
- support natif du streaming
- async/await
- typage Python strict
- performances proches de Node.js ou Go

### Structure de l'API
L'API propose :
- un modele de requete avec `text`, `model`, `task`
- un modele de reponse avec `result`, `model`, `tokens_per_sec`, `latency_s`
- un endpoint `/nlp/process`

### Taches NLP
Taches de base :
- resume
- extraction d'entites
- classification de documents
- mots cles en JSON

Taches avancees :
- Q&A sur document
- sentiment analysis
- traduction ou reformulation
- resume executif structure
- detection de langue

### Streaming avec FastAPI
Le document montre :
- l'usage de `StreamingResponse`
- des Server-Sent Events
- un flux token par token depuis Ollama
- l'interet UX du streaming

### Pourquoi benchmarker
Le benchmark sert a :
- choisir le modele optimal pour chaque tache
- mesurer le compromis vitesse/qualite
- identifier les limites
- justifier un choix technique avec des donnees

Metriques cles :
- tokens par seconde
- latence
- RAM utilisee
- score humain
- coherence JSON
- BLEU / ROUGE si reference disponible
- taux d'hallucination

### Corpus de test
Un corpus doit contenir :
- le texte d'entree
- la tache a effectuer
- une reference si possible
- des metadonnees comme langue, domaine, longueur

Le document recommande :
- 10 a 20 echantillons par tache minimum
- des textes courts et longs
- plusieurs langues
- plusieurs domaines
- des cas limites

### Evaluation qualitative
Grille de notation humaine :
- pertinence
- precision
- format
- concision
- hallucination oui/non

Le score global est la moyenne des 4 premiers criteres.

### Exemple de resultats attendus
Un tableau compare les modeles sur :
- tokens/s
- latence
- RAM
- qualite
- JSON OK
- commentaire global

### Prompt engineering
Bonnes pratiques donnees :
- donner un role au modele
- etre precis sur le format de sortie
- utiliser des exemples
- decomposer les taches complexes
- iterer
- specifier la langue de reponse

### Ressources et concepts
Concepts a maitriser :
- LLM / SLM
- quantization INT4 / INT8
- prompt engineering
- RAG
- embeddings
- format GGUF
- temperature / top-p

### Planning suggere
Semaines 1-2 :
- decouverte
- Ollama et tests CLI
- premiers appels API

Semaines 3-4 :
- projet FastAPI
- 3 taches NLP minimum
- streaming
- tests via Swagger

Semaines 5-6 :
- corpus de test
- mesures vitesse / RAM / qualite
- evaluation humaine
- graphiques et tableaux

Semaine 7 :
- demo complete
- rapport final
- exploration RAG en bonus

### Livrables attendus
Code :
- API FastAPI documentee
- au moins 3 taches NLP
- streaming
- tests unitaires
- module de benchmark
- export CSV + PNG
- corpus versionne

Documents :
- README
- rapport de benchmark
- presentation de demo finale

### Competences acquises
Le projet fait gagner :
- maitrise des SLMs en local
- API FastAPI et Python async
- prompt engineering
- benchmark rigoureux
- bases du RAG et des embeddings
- analyse de donnees avec Pandas et Matplotlib

## 2. T esting Agentique d'un Agent Conversationnel Web & Mobile

### Objectif general
Le second projet presente un systeme de testing agentique pour un agent conversationnel web et mobile, pilote par OpenAI Swarm et Ollama.

### Pourquoi le testing agentique
Problemes identifies :
- hallucinations
- differences entre Web et Mobile
- degradations silencieuses apres mise a jour
- casse sur inputs inattendus
- volume de cas difficilement lisible par humain

La solution : utiliser des agents IA pour generer, executer, evaluer et reporter des tests automatiquement.

### Spectre du testing
Le document distingue :
- unit test
- API testing
- browser use
- mobile use

Le projet couvre API supervisee + browser use + mobile use autonomes via Swarm Agents.

### Pourquoi Swarm
Swarm est presente comme un framework minimaliste d'orchestration multi-agents base sur :
- Agent = un SLM + instructions + outils
- Handoff = passage de relais entre agents

Comparaison avec LangGraph :
- courbe d'apprentissage plus faible
- moins verbeux
- bon pour prototypage rapide

### Reseau de handoff
Le cycle est :
- Generator Agent
- Executor Agent
- Evaluator Agent
- Reporter Agent

Chaque agent a une seule responsabilite.

### Architecture globale
Le systeme inclut :
- agent conversationnel cible
- Swarm orchestrator
- SLM local via Ollama
- screenshots, DOM, logs, DB
- actions Playwright ou Appium
- rapport final HTML ou Markdown

### Les 3 canaux d'execution
Canal 1 - API REST :
- endpoint chat
- httpx + pytest
- tests rapides
- validations schema JSON, timeout, 5xx, inputs malformes

Canal 2 - Web :
- interface chat web
- Playwright
- navigation DOM complete
- screenshot apres chaque action
- detection de crash et spinner infini

Canal 3 - Mobile :
- app Android/iOS
- Appium
- tap, swipe, scroll
- capture ecran apres action
- coherence Web versus Mobile

### Tools vs Code
Le document defend l'approche code-based.

Approche tool-based :
- click(selector)
- fill(selector, value)
- drag(from, to)
- new_tab(url)

Problemes :
- impossible de predefinir toutes les actions
- latence cumulee elevee
- fragile sur SPA et UI dynamiques
- maintenance difficile

Approche code-based :
- l'agent genere directement du code Playwright ou Appium
- un seul appel LLM pour un scenario complet
- rejouable, versionnable, diffable
- waits, retries et assertions natives

### Generator Agent
Role : generer les cas de test.

Sortie attendue :
- JSON valide
- champs id, canal, input utilisateur, contexte, resultat attendu, criteres d'echec
- cas nominaux, limites, vides, hors-domaine

### Executor Agent
Role : executer les cas de test selon le canal.

Il contient :
- execution API via httpx
- execution Web via Playwright
- execution Mobile via Appium
- retour des resultats bruts pour evaluation

### Evaluator Agent
Role : evaluer chaque test.

Criteres :
- pertinence
- exactitude
- hallucination
- coherence

Regles FAIL :
- hallucination vraie
- score moyen trop faible
- status HTTP >= 400

### Reporter Agent
Role : produire un rapport Markdown avec :
- resume global
- tableau des resultats
- top 3 echecs critiques
- comparaison Web vs API
- recommandations

### Testing mobile
Le document montre un exemple Appium avec :
- configuration emulateur Android
- lancement du driver
- saisie dans le champ chat
- clic sur envoyer
- attente de la reponse
- capture d'ecran
- fermeture du driver

### Metriques
Metriques automatiques :
- temps de reponse
- taux de timeout
- disponibilite
- BLEU / ROUGE
- coherence JSON
- detection d'hallucination

Metriques de l'Evaluator :
- pertinence
- exactitude factuelle
- coherence contexte
- format de sortie

Flags bloquants :
- hallucination
- crash UI / erreur 5xx
- divergence Web vs Mobile superieure a 20 %

### Exemple de rapport
Un tableau type compare :
- scenario
- canal
- latence
- score
- hallucination
- verdict

Le texte insiste sur le fait qu'un input vide mal gere ou une hallucination sur des chiffres doivent etre consideree comme des FAIL critiques.

### Prompt engineering pour agents de test
Bon prompt :
- role explicite QA senior
- input / expected / actual / canal
- sortie JSON stricte
- seuil de FAIL explicite

### Planning 7 semaines
S1-S2 :
- lecture Swarm / Playwright / Appium / Ollama
- installation des SLMs
- tests manuels
- ecriture de cas JSON

S3-S4 :
- pipeline Swarm complet
- Generator, Executor, Evaluator, Reporter
- pipeline end-to-end
- debug des handoffs et du parsing JSON

S5-S6 :
- integration Playwright
- integration Appium
- screenshots
- comparaison Web vs Mobile

S7 :
- rapport final
- dashboard HTML
- demo live
- piste CI/CD

### Livrables attendus
Code :
- pipeline Swarm complet
- canaux API, Web et Mobile
- export JSON et Markdown
- corpus de test de 50+ scenarios

Documents :
- README
- rapport de testing
- presentation et demo live

Critere de succes :
- detection automatique des regressions entre deux versions de l'agent cible.

### Competences acquises
Le projet enseigne :
- testing autonome pilote par LLM
- orchestration multi-agents
- automation browser et mobile
- prompt engineering QA strict
- usage de SLMs locaux pour pipelines prives
- detection objective d'hallucination
- convergence entre QA Engineering et AI Engineering

## 3. Tableau photo `tableau.jpg`

### Lecture generale
Le tableau photo ressemble a un schema de brainstorming sur :
- gouvernance / reglementation IA
- architecture d'agents
- couches de systeme
- chaines de traitement
- references a RGPD, GDPR, AI Act, modeles, APIs, agents

### Elements lisibles ou probables
J'ai pu distinguer plusieurs fragments :
- AI Act
- RGPD / GDPR
- SLM / agents
- API
- RAG
- modeles / memory
- streaming
- chaines de traitement
- prompts / agents
- compare / benchmark
- maybe pieces like HNWI, SDLC, RAI / RLSDC, call bot, API gateway, contextual security, etc.

### Transcription prudente
Comme la photo est prise de loin et avec des parties ecrites a la main, la transcription exacte n'est pas garantie. Le sens global semble etre :
- une architecture ou une carte mentale autour d'un systeme IA local
- des couches allant du modele aux API, aux agents et aux usages
- une partie sur la securite, la gouvernance et la conformite
- une partie sur l'exploitation pratique via call bot / apps / API

### Interpretation utile
Le tableau semble servir de support de reflexion pour relier :
- besoins metiers
- contraintes legales
- couche modele
- couche orchestration agentique
- couche API / produit
- evaluation / benchmark

## 4. Synthese globale

Les deux PDF forment un ensemble coherent autour de l'IA appliquee en local :
- le premier PDF pose une base technique pour faire tourner des SLMs avec Ollama, les exposer avec FastAPI et les benchmarker.
- le second PDF pousse la logique plus loin avec une orchestration multi-agents Swarm pour tester automatiquement un agent conversationnel sur Web, API et Mobile.

En resume :
- premier projet = construire et comparer des SLMs locaux
- second projet = utiliser des agents pour tester automatiquement d'autres agents
- le tableau photo = carte de reflexion complementaire sur l'architecture, la reglementation et les couches du systeme

## 5. Points d'action derives

Si tu veux transformer ce contenu en travail concret, les prochaines etapes naturelles sont :
- extraire un plan de projet unique a partir des deux supports
- faire un README de synthese plus court et plus propre
- transformer les slides en checklist de realisation
- refaire la transcription du tableau avec une photo plus proche si tu veux une version plus fidele
