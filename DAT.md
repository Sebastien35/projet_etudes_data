# Document d'Architecture Technique (DAT) — Projet d'études M1 Data

**Projet :** M1 Data Science — Plateforme de détection automatisée d'infox (*fake news*) sur le réseau Bluesky
**Version :** 2026-06-18 — branche `develop`

---

## Table des matières

- [Document d'Architecture Technique (DAT) — Projet d'études M1 Data](#document-darchitecture-technique-dat--projet-détudes-m1-data)
  - [Table des matières](#table-des-matières)
  - [1. Vue d'ensemble \& Architecture Générale](#1-vue-densemble--architecture-générale)
  - [2. Structure du Dépôt](#2-structure-du-dépôt)
  - [3. Stack Technologique](#3-stack-technologique)
  - [4. Infrastructure \& Conteneurisation (Docker)](#4-infrastructure--conteneurisation-docker)
    - [Environnement de Production](#environnement-de-production)
    - [Ordonnancement du démarrage (`depends_on`)](#ordonnancement-du-démarrage-depends_on)
    - [Réseau interne](#réseau-interne)
    - [Mécanismes de Persistance (Volumes)](#mécanismes-de-persistance-volumes)
    - [Gestion de la Santé des Services (Healthchecks)](#gestion-de-la-santé-des-services-healthchecks)
  - [5. Pipelines de Données (Framework Kedro)](#5-pipelines-de-données-framework-kedro)
    - [5.1 Pipeline `ingest_from_bluesky`](#51-pipeline-ingest_from_bluesky)
      - [Algorithme d'ingestion](#algorithme-dingestion)
    - [5.2 Pipeline `nlp_transform`](#52-pipeline-nlp_transform)
      - [Logique de nettoyage incrémental](#logique-de-nettoyage-incrémental)
    - [5.3 Pipeline `vectorisation`](#53-pipeline-vectorisation)
      - [Mécanisme d'encodage et clustering](#mécanisme-dencodage-et-clustering)
    - [5.4 Pipeline `emotion_classification`](#54-pipeline-emotion_classification)
    - [5.5 Pipeline `train_reliability` (Exécution Asynchrone / Ponctuelle)](#55-pipeline-train_reliability-exécution-asynchrone--ponctuelle)
    - [5.6 Pipeline `train_finetuned` (Exécution Ponctuelle)](#56-pipeline-train_finetuned-exécution-ponctuelle)
  - [6. Couche de Persistance (MongoDB)](#6-couche-de-persistance-mongodb)
    - [Schéma logique des collections](#schéma-logique-des-collections)
  - [7. Green IT \& Monitoring Énergétique (EnergyHook)](#7-green-it--monitoring-énergétique-energyhook)
  - [8. Couche Applicative \& API de Classification (FastAPI)](#8-couche-applicative--api-de-classification-fastapi)
    - [Mécanisme de démarrage (Lifespan)](#mécanisme-de-démarrage-lifespan)
    - [Spécification des Points d'Accès (Endpoints)](#spécification-des-points-daccès-endpoints)
      - [`POST /ask`](#post-ask)
      - [`POST /emotion`](#post-emotion)
      - [`GET /health`](#get-health)
      - [`GET /metrics`](#get-metrics)
  - [9. Services Partagés (`shared/`)](#9-services-partagés-shared)
  - [10. Interface Utilisateur (Streamlit)](#10-interface-utilisateur-streamlit)
    - [Architecture fonctionnelle des sections](#architecture-fonctionnelle-des-sections)
      - [Onglet 1 : Fact-Check (Espace de dialogue interactif)](#onglet-1--fact-check-espace-de-dialogue-interactif)
      - [Onglet 2 : Analytics (Statistiques du corpus)](#onglet-2--analytics-statistiques-du-corpus)
      - [Onglet 3 : Energy Report (Bilan environnemental)](#onglet-3--energy-report-bilan-environnemental)
    - [Identité Visuelle et Thémisation](#identité-visuelle-et-thémisation)
  - [11. Reverse Proxy \& Routage (Nginx)](#11-reverse-proxy--routage-nginx)
  - [12. Observabilité \& Monitoring (Prometheus \& Grafana)](#12-observabilité--monitoring-prometheus--grafana)
  - [13. Orchestration des Workflows (Apache Airflow)](#13-orchestration-des-workflows-apache-airflow)
    - [Schedules et orchestration des DAGs](#schedules-et-orchestration-des-dags)
    - [Processus d'initialisation de l'orchestrateur (Séquence de boot)](#processus-dinitialisation-de-lorchestrateur-séquence-de-boot)
  - [14. Intégration et Déploiement Continus (CI/CD)](#14-intégration-et-déploiement-continus-cicd)
  - [15. Configuration \& Variables d'Environnement](#15-configuration--variables-denvironnement)
  - [16. Cycle de Vie de la Donnée \& Flux de Bout en Bout](#16-cycle-de-vie-de-la-donnée--flux-de-bout-en-bout)
  - [17. Guide de Démarrage Rapide](#17-guide-de-démarrage-rapide)
    - [Prérequis Système](#prérequis-système)
    - [Déploiement en Environnement de Production (Hôte Linux)](#déploiement-en-environnement-de-production-hôte-linux)
    - [Déploiement en Environnement de Développement Local](#déploiement-en-environnement-de-développement-local)
    - [Exécution Manuelle et Séquentielle des Pipelines Data](#exécution-manuelle-et-séquentielle-des-pipelines-data)
    - [Extinction de l'Infrastructure](#extinction-de-linfrastructure)
  - [18. Limitations Connues \& Dette Technique](#18-limitations-connues--dette-technique)

---

## 1. Vue d'ensemble & Architecture Générale

**FakeShield** est une plateforme d'aide à l'analyse critique de l'information circulant sur le réseau social décentralisé **Bluesky**. Elle fournit à l'utilisateur deux signaux complémentaires sur tout texte soumis :

* un **score de crédibilité stylistique** (0–100 %) : mesure la proximité du texte avec le style rédactionnel de sources d'information vérifiées, entraîné sur un corpus labellisé par origine de source ;
* une **décomposition émotionnelle** (7 émotions d'Ekman) : quantifie la charge affective du contenu, signal reconnu dans la littérature sur la désinformation — les contenus manipulateurs étant statistiquement plus chargés en colère, peur ou dégoût.

> **Périmètre du système :** FakeShield ne prétend pas établir la vérité factuelle d'une affirmation. Il fournit des indicateurs d'aide à la lecture critique ; l'interprétation finale reste à la charge de l'utilisateur.

Le système s'articule autour de cinq pipelines de données managés, d'une API de classification en temps réel et d'un tableau de bord décisionnel.

L'écosystème respecte un paradigme architectural linéaire **ETL → ML → API → UI** :


```

Bluesky API
│  atproto (Recherche par mots-clés)
▼
MongoDB [Collection: posts]
│  Kedro nlp_transform
▼
MongoDB [Collection: cleaned_posts]
│  Kedro vectorisation puis emotion_classification (séquentiels dans __default__)
▼
MongoDB [Collection: classified_posts]   MongoDB [Collection: emotion_posts]
Artefacts (xlm_roberta_finetuned / ReliabilityClassifier / KMeans) ──► FastAPI (/ask, /emotion) ◄── Streamlit UI
│                                                                          │
Ollama LLM  (Interprétabilité NLP)                                        ▲
                                                                    Cascade (PRIMARY → FALLBACK1 → FALLBACK2)
```

---

## 2. Structure du Dépôt

```
projet_etudes_data/
├── conf/
│   ├── base/
│   │   ├── catalog.yml                        # Catalogue des Datasets Kedro
│   │   ├── parameters.yml                     # Paramètres globaux
│   │   ├── parameters_ingest_from_bluesky.yml
│   │   ├── parameters_nlp_transform.yml
│   │   ├── parameters_vectorisation.yml        # Hyperparamètres (clusters, features, artefacts)
│   │   └── parameters_emotion_classification.yml # Modèle DistilRoBERTa, batch_size, max_length
│   ├── airflow/                               # Configuration cible pour l'environnement Airflow
│   ├── grafana/
│   │   ├── provisioning/                      # Datasources & dashboards auto-provisionnés
│   │   └── dashboards/                        # Fichiers JSON des tableaux de bord Grafana
│   ├── nginx.conf                             # Configuration du Reverse Proxy
│   ├── prometheus.yml                         # Configuration du serveur de métriques
│   └── logging.yml                            # Stratégie de journalisation
├── data/
│   └── 06_models/                        # Sérialisation des modèles (Pickle)
├── dags/                                 # DAGs Airflow auto-générés par kedro-airflow
├── shared/                               # Composants transverses partagés (API, UI, Pipelines)
│   ├── mongo.py                          # Connecteur de persistance
│   ├── energy_service.py                 # Gestionnaire des métriques CodeCarbon
│   ├── finetuned_service.py              # Classifieur PRIMARY xlm-roberta-base fine-tuné
│   ├── kmeans_service.py                 # Moteur d'inférence KMeans (fallback)
│   ├── reliability_service.py            # Classifieur supervisé LogReg (embeddings + style features)
│   ├── embedding_service.py              # Encodage SentenceTransformer + extract_style_features
│   ├── emotion_inference_service.py      # Classifieur d'émotions temps-réel (DistilRoBERTa)
│   ├── ollama_service.py                 # Client d'inférence LLM local
│   ├── claude_service.py                 # Client d'inférence Claude (claude-agent-sdk)
│   ├── gemini_service.py                 # Solution LLM Cloud redondante
│   ├── rag.py                            # Module de recherche par similarité cosinus
│   ├── llm_interface.py                  # Contrat d'interface LLM
│   └── metrics.py                        # Définition des sondes Prometheus
├── src/
│   ├── api/
│   │   └── api.py                        # Point d'entrée FastAPI
│   ├── projet_etudes/
│   │   ├── hooks.py                      # Extensions Kedro (EnergyHook, SparkHooks)
│   │   ├── pipeline_registry.py          # Déclaration des points d'entrée des pipelines
│   │   └── settings.py                   # Paramètres de configuration Kedro
│   └── pipelines/
│       ├── ingest_from_bluesky/
│       ├── nlp_transform/
│       ├── vectorisation/
│       ├── emotion_classification/
│       ├── train_reliability/        # (intégré dans vectorisation/pipeline.py)
│       └── train_finetuned/          # Fine-tuning xlm-roberta-base (run5)
│   └── streamlit_app/
│       ├── streamlit_app.py              # Point d'entrée IHM (incl. render_emotion_chart)
│       ├── streamlit_logic.py            # Logique de présentation & requêtage (incl. analyze_message_emotion)
│       ├── streamlit_color_chart.py      # Thémisation graphique
│       ├── streamlit_config.py           # Configuration de l'IHM
│       └── config.toml                   # Paramètres natifs Streamlit
├── conf/
│   └── base/
│       ├── parameters_train_finetuned.yml # Hyperparamètres du fine-tuning xlm-roberta
│       └── ...
├── Dockerfile                            # Image Kedro — exécution des pipelines data
├── Dockerfile.api
├── Dockerfile.airflow
├── Dockerfile.streamlit
├── Dockerfile.docs                       # MkDocs Material — sert le DAT en HTML via nginx
├── docker-compose.yml
├── mkdocs.yml                            # Configuration de la documentation MkDocs
├── pyproject.toml                        # Gestion des dépendances du projet
└── Makefile                              # Raccourcis d'automatisation des tâches

```

---

## 3. Stack Technologique

| Couche | Technologie | Version / Cible | Rôle opérationnel |
| --- | --- | --- | --- |
| **Runtime** | Python | $\ge 3.10, < 3.15$ | Environnement d'exécution unifié |
| **Package Management** | `uv` | *latest* | Gestionnaire de dépendances et de venv ultra-rapide |
| **Framework Data** | Kedro | ~1.0.0 | Structuration et modularité des pipelines data |
| **Ingestion Réseau** | `atproto` | 0.0.63 | Interaction avec le protocole décentralisé Bluesky |
| **Persistance** | MongoDB | *latest* (PyMongo) | Base de données NoSQL orientée documents |
| **Machine Learning** | scikit-learn | ~1.5.1 | Clustering non supervisé (KMeans) et classification supervisée (LogisticRegression) |
| **NLP Transformers** | HuggingFace Transformers | *latest* | Classification d'émotions (DistilRoBERTa `j-hartmann/emotion-english-distilroberta-base`) |
| **Embeddings sémantiques** | Sentence-Transformers | ≥3.0.0 | Encodage dense multilingue (`paraphrase-multilingual-MiniLM-L12-v2`) pour le classifieur de fiabilité |
| **Classifieur supervisé** | scikit-learn LogisticRegression | ~1.5.1 | Classifieur de fiabilité entraîné sur embeddings (remplace KMeans comme classifieur principal) |
| **Service Web** | FastAPI | *latest* | Serveur d'API asynchrone avec validation Pydantic |
| **Serveur d'Inférence** | Uvicorn | *latest* | Serveur ASGI de production pour l'API |
| **LLM Local** | Ollama | *latest* | Moteur d'exécution pour le modèle `qwen2:1.5b` |
| **LLM Cloud (Failover)** | Google Gemini | *latest* | Solution LLM externe de secours via `google-genai` |
| **LLM Anthropic** | Claude (claude-agent-sdk) | claude-opus-4-6 | Alternative d'explication LLM via `claude-agent-sdk` (`ClaudeService`) |
| **Restitution / UI** | Streamlit | *latest* | Dashboard de restitution de données en temps réel |
| **Dataviz** | Altair | *latest* | Génération de graphiques déclaratifs interactifs |
| **Documentation** | MkDocs Material | 9 | Site de documentation statique servi en conteneur |
| **Green IT** | CodeCarbon | *latest* | Évaluation des émissions de $CO_2$ et de la puissance consommée |
| **Collecte Métriques** | Prometheus | *latest* | Base de données temporelle pour le monitoring technique |
| **Visualisation Métriques** | Grafana | *latest* | Tableaux de bord de supervision technique |
| **Orchestration Workflow** | Apache Airflow | 2.8.4 | Ordonnancement et supervision des tâches ETL |
| **Serveur Frontal / Proxy** | Nginx | *alpine* | Reverse proxy et routage HTTP (HTTP uniquement, pas de TLS) |
| **RDBMS Airflow** | MariaDB | *latest* | Base de données de gestion d'états pour Airflow |
| **Conteneurisation** | Docker / Compose | v2 | Isolation et portabilité de la stack applicative |
| **Qualité Code** | Ruff | ~0.12.0 | Linter et formateur (`ruff check` + `ruff format`) |
| **Audit Dockerfiles** | `hadolint` | v3.1.0 | Lint statique des Dockerfiles en CI |
| **Tests** | pytest / pytest-cov | ~7.2 | Automatisation des tests et couverture de code |

---

## 4. Infrastructure & Conteneurisation (Docker)

### Environnement de Production

L'application est actuellement déployée sur une instance cloud **AWS EC2 (Amazon Linux 2023)** managée via **Docker Compose v2**. L'intégration est entièrement automatisée : tout déploiement est instancié suite à la validation du pipeline CI/CD via une connexion SSH sur la cible.

> **Portabilité infrastructure :** Le déploiement repose exclusivement sur SSH + Docker Compose, sans aucun outil d'IaC spécifique au cloud (Terraform, CloudFormation, CDK…) ni dépendance à des services AWS managés (RDS, ECS, S3…). La stack est donc **cloud-agnostique** et peut être transposée sans modification sur n'importe quel hôte Linux disposant de Docker : serveur on-premise, VPS chez un autre fournisseur (GCP, Azure, Hetzner…) ou machine locale. Seule la valeur du secret `EC2_HOST` dans le pipeline CI/CD est à mettre à jour pour pointer vers la nouvelle cible.

> **Note MongoDB :** La base de données **MongoDB Atlas** (cloud managé) est une dépendance **externe** au Docker Compose. Elle n'est pas conteneurisée localement. La connexion s'effectue via l'URI `MONGO_CONNECTION_STRING` injectée dans le `.env`. Tous les services qui lisent ou écrivent en base dépendent donc d'une connectivité réseau sortante vers Atlas.

L'écosystème applicatif est segmenté en micro-services isolés :

| Service Docker | Source d'Image | Port Hôte | Port Conteneur | Responsabilité Métier |
| --- | --- | --- | --- | --- |
| `nginx` | `nginx:alpine` | 80 | 80 | Point d'entrée unique du trafic (Reverse Proxy) |
| `docs` | `Dockerfile.docs` | — | 80 | Site de documentation statique (MkDocs → nginx interne) |
| `airflow-webserver` | `Dockerfile.airflow` | — | 8080 | Interface web d'administration d'Airflow |
| `airflow-scheduler` | `Dockerfile.airflow` | — | — | Planificateur et exécuteur de tâches |
| `airflow-init` | `Dockerfile.airflow` | — | — | Initialisation de la base de données relationnelle |
| `database` | `mariadb:latest` | 3360 | 3306 | Stockage d'état et métadonnées Airflow |
| `ollama` | `ollama/ollama` | — | 11434 | Inférence locale du LLM (Réseau interne uniquement) |
| `api` | `Dockerfile.api` | 8080 | 8080 | Point d'accès d'inférence de classification (FastAPI) |
| `streamlit` | `Dockerfile.streamlit` | — | 8501 | Interface utilisateur Web |
| `prometheus` | `prom/prometheus` | 9090 | 9090 | Serveur de scrutation (*scraping*) des métriques |
| `grafana` | `grafana/grafana` | 3000 | 3000 | Visualisation avancée des données techniques |
| `node-exporter` | `prom/node-exporter` | — | — | Collecteur de métriques matérielles de l'hôte |

### Ordonnancement du démarrage (`depends_on`)

```
nginx ─────────────┬──► streamlit
                   └──► docs
streamlit ─────────────► api (Statut de santé requis)
api ────────────────────► ollama (Statut de santé requis)
prometheus ─────────────► api
                    └──► node-exporter
grafana ────────────────► prometheus
airflow-webserver ──────► airflow-init (Statut: success requis)
airflow-scheduler ──────► airflow-init (Statut: success requis)
airflow-init ───────────► database

```

> Note : `airflow-webserver` n'est pas dans les `depends_on` de `nginx` (commenté dans `docker-compose.yml`). L'UI Airflow est accessible via le proxy mais nginx ne bloque pas son démarrage sur la disponibilité d'Airflow.

### Réseau interne

Docker Compose crée automatiquement un réseau bridge dédié (`projet_etudes_data_default`). Les services se découvrent entre eux par leur **nom de service** (`api`, `ollama`, `streamlit`, etc.). Aucun port inter-service n'est exposé sur l'hôte sauf ceux listés dans la colonne "Port Hôte" ci-dessus.

### Mécanismes de Persistance (Volumes)

* `airflow-logs` & `airflow-plugins` : Conservation des journaux applicatifs et extensions d'orchestration.
* `ollama-data` : Persistance locale des poids du modèle LLM (`qwen2:1.5b`), évitant les téléchargements redondants au démarrage.
* `hf-cache` : Cache des modèles HuggingFace (`~/.cache/huggingface`) partagé entre les redéploiements du conteneur `api`. Évite le re-téléchargement du modèle DistilRoBERTa d'émotion à chaque build.
* `./data` (Volume lié à l'hôte) : Monté au sein du conteneur `api` pour assurer l'accès aux modèles sérialisés par Kedro (`.pkl`).

### Gestion de la Santé des Services (Healthchecks)

Le service `ollama` implémente une routine de démarrage robuste. Il instancie le démon `ollama serve` puis orchestre le téléchargement du modèle via `ollama pull qwen2:1.5b` (volume d'environ 900 Mo). La sonde de santé vérifie périodiquement la disponibilité du modèle via `ollama list | grep qwen2`, avec un `start_period` de **300 secondes** suivi de **20 tentatives** espacées de **15 secondes** — soit un délai maximal total d'environ **600 secondes** avant que le service ne soit déclaré en échec.

Le service `api` dispose d'un `start_period` porté à **60 secondes** (contre 15 précédemment) afin de laisser le temps au mécanisme de lifespan FastAPI de pré-charger le modèle d'émotion DistilRoBERTa avant que les sondes de santé ne soient déclarées actives.

---

## 5. Pipelines de Données (Framework Kedro)

Le framework **Kedro 1.0.0** est utilisé comme colonne vertébrale pour structurer le code de traitement de données. Six pipelines sont enregistrés dans `pipeline_registry.py` : `ingest_from_bluesky`, `nlp_transform`, `vectorisation`, `train_reliability`, `emotion_classification` et `train_finetuned`.

Par défaut, le pipeline `__default__` exécute le cycle ETL complet :

$$\text{ingest\_from\_bluesky} \longrightarrow \text{nlp\_transform} \longrightarrow \text{vectorisation} \longrightarrow \text{emotion\_classification}$$

Les pipelines `train_reliability` et `train_finetuned` sont isolés de la routine `__default__` : ils s'exécutent en ponctuel (`make run3` et `make run5`) pour générer les artefacts ML avant que l'API puisse utiliser les classifieurs supervisés.

```mermaid
flowchart LR
    BS(["🌐 API Bluesky"])
    M1[("MongoDB\nposts")]
    M2[("MongoDB\ncleaned_posts")]
    M3[("MongoDB\nclassified_posts")]
    M4[("MongoDB\nemotion_posts")]
    PKL[("data/06_models/\n*.pkl")]

    subgraph P1["Pipeline : ingest_from_bluesky"]
        N1a["fetch_from_reliable_accounts"]
        N1b["fetch_from_keywords"]
        N1c["merge_posts"]
        N2["save_posts_to_db"]
        N1a --> N1c
        N1b --> N1c
        N1c --> N2
    end

    subgraph P2["Pipeline : nlp_transform"]
        N3["get_posts_to_treat"]
        N4["clean_text\n(+ extract_style_features avant nettoyage)"]
        N5["normalize_text"]
        N6["save_to_db\n(incl. style_features)"]
        N3 --> N4 --> N5 --> N6
    end

    subgraph P3["Pipeline : vectorisation"]
        N7["get_cleaned_posts"]
        N8["encode_texts\nSentenceTransformer (384-dim) + style (5-dim) → 389-dim"]
        N9["cluster_posts\nKMeans (k=2)"]
        N10["save_model_artifacts"]
        N11["save_predictions"]
        N7 --> N8 --> N9
        N9 --> N10
        N9 --> N11
    end

    subgraph P4["Pipeline : emotion_classification"]
        N12["get_posts_for_emotion\n(incrémental)"]
        N13["classify_emotions_bert\nDistilRoBERTa (7 émotions Ekman)"]
        N14["save_emotion_results"]
        N12 --> N13 --> N14
    end

    subgraph P5["Pipeline : train_finetuned (run5 — ponctuel)"]
        N15["get_finetuning_data"]
        N16["finetune_xlm_roberta\n(3 epochs, lr=2e-5, freeze all except last 2 layers)"]
        N15 --> N16
    end

    FT[("data/06_models/\nxlm_roberta_finetuned/")]

    BS --> N1a
    BS --> N1b
    N2 --> M1
    M1 --> N3
    N6 --> M2
    M2 --> N7
    M2 --> N12
    M2 --> N15
    N10 --> PKL
    N11 --> M3
    N14 --> M4
    N16 --> FT

```

### 5.1 Pipeline `ingest_from_bluesky`

* **Objectif :** Collecter les publications du réseau décentralisé Bluesky via deux stratégies complémentaires — sources fiables et mots-clés thématiques — et assurer leur persistance brute avec un label de fiabilité attaché à chaque post.
* **Composants (Nodes) :**
  * `fetch_from_reliable_accounts_node` : Collecte directement les posts de comptes vérifiés (Reuters, AFP, BBC, Le Monde, NYT…) et les étiquette `source_label = "reliable"`.
  * `fetch_from_keywords_node` : Interroge l'API par axes thématiques et attribue `source_label = "reliable"` ou `"unverified"` selon le domaine de l'auteur.
  * `merge_posts_node` : Fusionne les deux listes en dédupliquant sur `unique_id`.
  * `save_posts_to_db_node` : Insère le corpus consolidé en base de données.



#### Algorithme d'ingestion

1. **Authentification :** Connexion via la bibliothèque `atproto.Client.login()` en exploitant les variables d'environnement `BSKY_USERNAME` et `BSKY_APP_PASSWORD`.
2. **Voie 1 — Sources fiables :** Récupération directe des $N$ derniers posts des comptes listés dans `parameters_ingest_from_bluesky.yml` (`reliable_accounts`). Chaque post est immédiatement étiqueté `source_label = "reliable"`.
3. **Voie 2 — Mots-clés thématiques :** Requêtage structuré autour de quatre axes :
   * *Discover :* `news`, `world news`, `science`, `technology`, `research`
   * *Trending :* `breaking news`, `urgent`, `live updates`, `alert`
   * *Hot Topics :* `politics`, `election`, `climate`, `crisis`, `economy`, `AI`
   * *Misinformation :* `fact check`, `debunked`, `misinformation`, `conspiracy`, `hoax`

   Chaque post est étiqueté `"reliable"` si le domaine de l'auteur figure dans `reliable_domains`, sinon `"unverified"`.
4. **Déduplication & Intégrité :** Génération d'un identifiant composite unique `{username}_{created_at}`. Les doublons intra-requête sont éliminés et les publications sans texte ou métadonnées temporelles sont écartées.
5. **Persistance brute :** Opération d'écriture groupée (`insert_many`) au sein de la collection `posts`.

> **Note :** Le champ `source_label` stocké dans `posts` est la source de vérité pour l'entraînement du classifieur de fiabilité (`train_reliability`). Les posts `"reliable"` servent de labels positifs, les posts de catégorie `"Misinformation"` de labels négatifs.

* **Commande d'activation :** `kedro run --pipeline=ingest_from_bluesky` (ou via le raccourci `make run1`).

---

### 5.2 Pipeline `nlp_transform`

* **Objectif :** Nettoyer, normaliser et harmoniser les publications brutes afin de minimiser le bruit textuel avant la phase de modélisation.
* **Composants (Nodes) :**
* `get_posts_to_treat_node` : Extraction différentielle des nouvelles données.
* `clean_text_node` : Application des expressions régulières de nettoyage.
* `normalize_text_node` : Standardisation morphologique et textuelle.
* `save_to_db_node` : Persistance au sein de la collection intermédiaire.



#### Logique de nettoyage incrémental

La fonction `get_posts_to_treat` isole uniquement les documents de la collection `posts` dont l'identifiant `unique_id` n'apparaît pas encore dans `cleaned_posts`.

Le processus applique successivement deux niveaux de traitement sur le contenu textuel :

```
[Texte Brut]
   │
   ├──► extract_style_features() → 5 features stylistiques (AVANT tout nettoyage)
   │    caps_ratio, exclamation_density, question_density, lexical_diversity, avg_word_length
   │
   ▼
1. Passage en minuscules
2. Élimination des URL (Regex : http\S+|www\S+)
3. Suppression des mentions (Regex : @\w+)
4. Suppression des hashtags (Regex : #\w+)
5. Filtrage des Emojis (Plages Unicode U+1F600–U+1F6FF, U+1F1E0–U+1F1FF)
6. Retrait des caractères de ponctuation (str.maketrans)
   │
   ▼
[Colonne : clean_text]
   │
   ▼
1. Décomposition Unicode standardisée NFKD
2. Encodage strict ASCII (omission des caractères non convertibles)
3. Normalisation des espaces (collapsage des espaces multiples)
   │
   ▼
[Colonne : normalized_text]

```

> **Extraction précoce des features stylistiques :** Les 5 features sont extraites sur le texte **brut** (avant nettoyage) car elles capturent des signaux de manipulation souvent détruits par le nettoyage — majuscules, ponctuation excessive, emojis. Elles sont stockées dans `cleaned_posts.style_features` et concaténées aux embeddings dans les pipelines `vectorisation` et `train_reliability`.

* **Commande d'activation :** `kedro run --pipeline=nlp_transform` (ou via `make run2`).

---

### 5.3 Pipeline `vectorisation`

* **Objectif :** Encoder le texte nettoyé en vecteurs denses, segmenter le corpus via K-Means non supervisé avec orientation dynamique des clusters, et exporter le modèle KMeans servant de classifieur de **repli** à l'API.
* **Configuration de référence (`conf/base/parameters_vectorisation.yml`) :**
```yaml
vectorisation:
  embedding_model: "paraphrase-multilingual-MiniLM-L12-v2"
  n_clusters: 2
  kmeans_path: "data/06_models/kmeans_model.pkl"
  reliability_classifier_path: "data/06_models/reliability_classifier.pkl"

```



#### Mécanisme d'encodage et clustering

Le pipeline extrait le texte normalisé des publications non encore classifiées. Les textes sont encodés en vecteurs denses via **SentenceTransformer** (modèle `paraphrase-multilingual-MiniLM-L12-v2`, configurable via le paramètre `embedding_model`). Cette approche sémantique remplace une ancienne vectorisation TF-IDF et produit des représentations multilingues L2-normalisées.

Les 5 features stylistiques stockées dans `cleaned_posts.style_features` sont ensuite concaténées aux embeddings pour former une **matrice de features à 389 dimensions** (384 embeddings + 5 style features). Les style features sont récupérées depuis le document MongoDB et utilisées directement — elles ont été calculées lors du pipeline `nlp_transform`.

La matrice $X$ (389-dim) est soumise à un partitionnement via l'algorithme des **K-Means** ($k=2$).

> **Orientation dynamique des clusters :**
> L'identité "real" et "fake" des clusters n'est pas fixée arbitrairement. À l'issue du clustering, chaque cluster reçoit un score :
>
> $$\text{score}(c) = \text{reliable\_rate}(c) - \text{misinfo\_rate}(c)$$
>
> où `reliable_rate` est la proportion de posts `source_label = "reliable"` dans le cluster, et `misinfo_rate` la proportion de posts de catégorie `"Misinformation"`. **Le cluster au score le plus élevé est désigné "real"** (`is_real = True`), l'autre "fake" (`is_real = False`). Cette règle est indépendante de l'indice numérique du cluster (0 ou 1).

Le score de confiance par post est calculé à partir des distances aux centroïdes :

$$\text{Score} = \frac{d(\mathbf{x}, \mathbf{c}_{\text{fake}})}{d(\mathbf{x}, \mathbf{c}_{\text{fake}}) + d(\mathbf{x}, \mathbf{c}_{\text{real}}) + \varepsilon}$$

*Où $\varepsilon = 10^{-8}$ est une constante de stabilité numérique. Un score élevé indique une forte probabilité de véracité.*

Le modèle KMeans est sérialisé dans `data/06_models/kmeans_model.pkl`. Les résultats d'inférence sont insérés via `bulk_write` (`UpdateOne` + `upsert=True`) dans la collection `classified_posts`.

* **Commande d'activation :** `kedro run --pipeline=vectorisation` (ou via `make run3`, qui enchaîne aussi `train_reliability`).

---

### 5.4 Pipeline `emotion_classification`

* **Objectif :** Classer l'émotion dominante de chaque publication nettoyée à l'aide d'un modèle pré-entraîné basé sur BERT. Le pipeline est **incrémental** : seuls les posts dont l'identifiant n'est pas encore présent dans la collection `emotion_posts` sont traités.
* **Composants (Nodes) :**
  * `get_posts_for_emotion_node` : Extraction différentielle depuis `cleaned_posts` en soustrayant les `unique_id` déjà présents dans `emotion_posts`.
  * `classify_emotions_bert_node` : Inférence par lots via le modèle `j-hartmann/emotion-english-distilroberta-base`.
  * `save_emotion_results_node` : Upsert transactionnel dans `emotion_posts`.

#### Modèle et taxonomie émotionnelle

Le modèle utilisé est un **DistilRoBERTa** fine-tuné sur 6 datasets couvrant les 7 émotions d'Ekman :

| Émotion | Couleur d'accentuation |
| --- | --- |
| `joy` | Vert émeraude `#34d399` |
| `surprise` | Violet `#c084fc` |
| `neutral` | Gris bleuté `#7878a0` |
| `fear` | Orange `#fb923c` |
| `sadness` | Bleu `#60a5fa` |
| `anger` | Rouge `#f87171` |
| `disgust` | Gris ardoise `#94a3b8` |

Le traitement s'effectue par batches configurables (`batch_size`). Les paramètres de référence (`conf/base/parameters_emotion_classification.yml`) incluent le nom du modèle, la longueur maximale des séquences et la taille de batch.

* **Commande d'activation :** `kedro run --pipeline=emotion_classification` (intégré dans `__default__`).

---

### 5.5 Pipeline `train_reliability` (Exécution Asynchrone / Ponctuelle)

* **Objectif :** Entraîner un classifieur de fiabilité supervisé sur des labels terrain issus de l'ingestion, qui devient le **classifieur principal** exposé par l'API (remplaçant KMeans).
* **Architecture :**
  1. Extraction depuis `cleaned_posts` en utilisant le champ `source_label` comme label de vérité terrain :
     * Posts `source_label = "reliable"` → label 1 (vrai)
     * Posts de catégorie `"Misinformation"` → label 0 (faux)

     > Cette approche évite la circularité des pseudo-labels KMeans : les labels sont ancrés sur l'identité des sources (comptes vérifiés vs. thème "misinformation"), pas sur le clustering.

  2. Encodage dense via `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2`) — vecteurs L2-normalisés (384-dim).
  3. Concaténation des **5 features stylistiques** déjà stockées dans `cleaned_posts.style_features` → matrice finale **389-dim** (384 + 5).
  4. Entraînement d'une `LogisticRegression` (scikit-learn) avec `class_weight="balanced"` et validation croisée ROC-AUC (5-fold) sur la matrice 389-dim.
  5. Sérialisation du classifieur dans `data/06_models/reliability_classifier.pkl`.

Le score ROC-AUC est journalisé à l'issue de l'entraînement. Ce pipeline est inclus dans `kedro run --pipeline=vectorisation` (via `make run3`) et peut aussi être exécuté isolément.

* **Commande d'activation :** `kedro run --pipeline=train_reliability` (ou via `make run3` qui l'enchaîne après vectorisation).

---

### 5.6 Pipeline `train_finetuned` (Exécution Ponctuelle)

* **Objectif :** Fine-tuner le modèle `xlm-roberta-base` sur les posts Bluesky labellisés afin de produire le **classifieur PRIMARY** de la cascade API. Plus précis que `ReliabilityService` (LogReg) lorsqu'un corpus suffisant est disponible.
* **Composants (Nodes) :**
  * `get_finetuning_data_node` : Extraction depuis `cleaned_posts` — même logique de labels que `train_reliability` (`source_label = "reliable"` → 1, catégorie `"Misinformation"` → 0). Lève `ValueError` si le corpus est insuffisant (seuil configurable : `min_reliable=30`, `min_misinfo=30`).
  * `finetune_xlm_roberta_node` : Fine-tuning via HuggingFace `Trainer`.

* **Stratégie de fine-tuning :**
  1. Chargement de `xlm-roberta-base` (classification à 2 classes).
  2. **Gel sélectif des paramètres** : tous les paramètres sont gelés, puis seuls les 2 dernières couches de l'encodeur (`roberta.encoder.layer.10`, `roberta.encoder.layer.11`) et la tête de classification sont dégelées — évite l'overfitting sur les petits corpus.
  3. Split 80/20 train/val (stratifié).
  4. Entraînement avec `eval_strategy="epoch"`, `load_best_model_at_end=True`, métrique pilote : **ROC-AUC**.
  5. Métriques journalisées : `roc_auc` + `accuracy` par epoch.
  6. Sauvegarde du modèle et du tokenizer dans `data/06_models/xlm_roberta_finetuned/` (format HuggingFace natif).

* **Configuration de référence (`conf/base/parameters_train_finetuned.yml`) :**

```yaml
train_finetuned:
  model_name: "xlm-roberta-base"
  max_length: 128
  batch_size: 16
  num_epochs: 3
  learning_rate: 2.0e-5
  unfreeze_layers: ["roberta.encoder.layer.11", "roberta.encoder.layer.10", "classifier"]
  model_path: "data/06_models/xlm_roberta_finetuned"
  min_reliable: 30
  min_misinfo: 30
```

> **Note :** Ce pipeline est intentionnellement exclu du `__default__` (ETL de routine). Il nécessite un corpus suffisant et un temps d'entraînement significatif (CPU-only : plusieurs heures). Il est déclenché manuellement via `make run5` une fois le corpus constitué.

* **Commande d'activation :** `kedro run --pipeline=train_finetuned` (ou via `make run5`).

---

## 6. Couche de Persistance (MongoDB)

L'application centralise ses données au sein d'une instance **MongoDB Atlas** (cloud managé, externe au Docker Compose) nommée `bluesky_db`. Les accès clients sont initialisés par le module partagé `shared/mongo.py` à l'aide de l'URI de connexion injectée via la variable d'environnement `MONGO_CONNECTION_STRING`.

### Schéma logique des collections

```
bluesky_db (Base de données)
  ├── posts (Publications brutes)
  │     └── [ _id, unique_id, username, text, created_at, category, source_label, utc_saved_at ]
  │           source_label ∈ { "reliable", "unverified" } — attribué à l'ingestion selon la source
  │
  ├── cleaned_posts (Publications prétraitées par NLP)
  │     └── [ _id, unique_id, username, created_at, category, source_label, normalized_text, style_features: [5 floats], utc_saved_at ]
  │           style_features = [caps_ratio, exclamation_density, question_density, lexical_diversity, avg_word_length]
  │
  ├── classified_posts (Résultats d'inférence KMeans/Reliability)
  │     └── [ _id, unique_id, username, category, normalized_text, fake_news_prob, is_real, cluster, classified_at ]
  │
  ├── emotion_posts (Résultats d'inférence DistilRoBERTa — Ekman 7, batch pipeline)
  │     └── [ _id, unique_id, username, category, normalized_text, emotion, emotion_score, classified_at ]
  │           ⚠ Stocke uniquement l'émotion dominante (top-1). L'endpoint /emotion retourne
  │             les 7 scores complets en temps réel sans passer par cette collection.
  │
  └── energy_logs (Traces de consommation CodeCarbon)
        └── [ _id, pipeline_name, node_name, run_id, timestamp, duration_s, energy_kwh, co2_kg, ... ]

```

---

## 7. Hooks Kedro (MongoIndexHook & EnergyHook)

Le projet étend le cycle de vie Kedro via deux hooks déclarés dans `src/projet_etudes/hooks.py`.

### MongoIndexHook

Avant le démarrage de chaque pipeline, `MongoIndexHook` crée automatiquement un index sur le champ `unique_id` pour les quatre collections principales (`posts`, `cleaned_posts`, `classified_posts`, `emotion_posts`). Cela garantit des performances de requête acceptables même sur des corpus larges, sans intervention manuelle.

```
[before_pipeline_run]
       │  Connexion MongoDB
       ▼
create_index("unique_id", background=True) × 4 collections
       │
       ▼
[Pipeline démarre]
```

Toute exception est interceptée et journalisée en `WARNING` — le pipeline n'est pas bloqué si la création d'index échoue.

### EnergyHook (Green IT)

Afin d'intégrer les problématiques d'éco-conception logicielle (Green IT), le projet intègre un mécanisme d'audit énergétique systématique via l'implémentation de la classe `EnergyHook`, qui s'exécute autour de chaque nœud Kedro.

```
[Début du Pipeline]
       │  Extraction du paramètre run_params["pipeline_name"]
       ▼
[Avant exécution d'un Node]
       │  Instanciation de CodeCarbon : EmissionsTracker(measure_power_secs=1)
       │  Initialisation de la scrutation matérielle (tracker.start())
       ▼
[Exécution du code métier du Node]
       │
       ▼
[Après exécution du Node]
       │  Arrêt du tracker (tracker.stop())
       │  Extraction des métriques (final_emissions_data)
       │  Appel à energy_service.save_energy_log()
       ▼
[Node Suivant ou Fin du Pipeline]

```

La couche d'instrumentation est conçue pour être totalement transparente et résiliente : toute exception générée par le framework CodeCarbon est interceptée, journalisée sous forme d'avertissement (`WARNING`), et ne bloque en aucun cas l'exécution des flux d'ingestion ou de calcul.

---

## 8. Couche Applicative & API de Classification (FastAPI)

Le service d'inférence est opéré par FastAPI sur le port `8080`. Il est démarré en production via l'environnement ASGI Uvicorn.

#### Mécanisme de démarrage (Lifespan)

Au démarrage de l'application, le gestionnaire de cycle de vie FastAPI (`lifespan`) :
1. Pré-charge le singleton `EmotionInferenceService` (téléchargement + chargement du modèle DistilRoBERTa en mémoire).
2. Envoie une requête de préchauffage (*warm-up*) à Ollama afin que la première vraie requête `/ask` ne subisse pas de latence de démarrage du LLM.

### Spécification des Points d'Accès (Endpoints)

#### `POST /ask`

Retourne le **score de crédibilité stylistique** d'un texte soumis par l'utilisateur, accompagné d'une explication en langage naturel.

> **Interprétation du score :** la valeur `probability` exprime la similarité stylistique du texte avec le corpus de sources vérifiées (Reuters, AFP, BBC…). Un score élevé indique que le texte ressemble à du contenu issu de médias fiables ; un score faible indique une proximité avec des contenus catégorisés "misinformation". Il ne s'agit **pas** d'une attestation de vérité factuelle.

* **Contrat d'entrée (JSON) :**
```json
{ "question": "L'affirmation textuelle à analyser" }
```

* **Logique métier interne :**
1. **Cascade de classifieurs (priorité décroissante) :**
   * **`FinetunedService` (PRIMARY)** : Inférence via `xlm-roberta-base` fine-tuné (`data/06_models/xlm_roberta_finetuned/`). Si le dossier n'existe pas (`FileNotFoundError`), repli automatique sur le niveau suivant.
   * **`ReliabilityService` (FALLBACK 1)** : Encodage du texte via `SentenceTransformer` (384-dim) + 5 style features extraites à la volée → 389-dim, puis prédiction de probabilité par `LogisticRegression`. Si `reliability_classifier.pkl` est absent, repli sur `KMeansService`.
   * **`KMeansService` (FALLBACK 2)** : Clustering non supervisé — dernier recours si aucun artefact supervisé n'est disponible.
2. **Traduction du score en niveau de crédibilité discret (`ProbabilityScoreModel`) :**
   * $\text{Score} \ge 0.60 \longrightarrow \text{"true"}$ — style très proche des sources fiables
   * $\text{Score} \ge 0.40 \longrightarrow \text{"very likely true"}$
   * $\text{Score} \ge 0.20 \longrightarrow \text{"uncertain"}$
   * $\text{Score} > 0 \longrightarrow \text{"very likely false"}$
   * $\text{Score} = 0 \longrightarrow \text{"false"}$ — style très proche des contenus misinformation
3. **Explication stylistique asynchrone (`OllamaService`) :** Sollicitation du LLM local `qwen2:1.5b` via `httpx.AsyncClient` (timeout 300 s). Le prompt détecte la langue du texte et produit 2-3 phrases décrivant les caractéristiques stylistiques qui ont influencé le score. En cas de défaillance d'Ollama, une chaîne vide est retournée sans bloquer la réponse.
4. **Télémétrie :** Incrémentation des compteurs Prometheus selon le niveau de crédibilité rendu.

* **Contrat de sortie (JSON) — voie principale (`FinetunedService`) :**
```json
{
  "verdict": "91% real",
  "probability": 0.9124,
  "based_on": "xlm_roberta_finetuned",
  "label": "true",
  "score_pct": 91,
  "explanation": "L'analyse linguistique met en évidence une structure syntaxique informative..."
}
```
* **Contrat de sortie (JSON) — voie de repli 1 (`ReliabilityService`) :**
```json
{
  "verdict": "true | very likely true | uncertain | very likely false | false",
  "probability": 0.9124,
  "based_on": "reliability_classifier",
  "label": "true",
  "score_pct": 91,
  "explanation": "..."
}
```
* **Contrat de sortie (JSON) — voie de repli 2 (`KMeansService`) :**
```json
{
  "verdict": "uncertain",
  "probability": 0.5,
  "based_on": "kmeans",
  "cluster": 1,
  "label": "uncertain",
  "score_pct": 50,
  "explanation": ""
}
```

#### `POST /emotion`

Analyse l'émotion dominante d'un texte libre en temps réel, indépendamment du pipeline Kedro.

* **Contrat d'entrée (JSON) :**
```json
{ "text": "Le texte à analyser" }
```

* **Logique :** Appel synchrone à `EmotionInferenceService.classify()` — retourne les 7 scores Ekman triés par confiance décroissante.

* **Contrat de sortie (JSON) :**
```json
{
  "emotions": [
    { "emotion": "joy",      "score": 0.7821 },
    { "emotion": "neutral",  "score": 0.1034 },
    ...
  ]
}
```

En cas d'erreur interne, retourne un `HTTP 500` avec le détail `"Emotion analysis unavailable"`.

#### `GET /health`

Renvoie un indicateur d'état nominal `"OK"`. Cet endpoint sert de sonde de vitalité (*liveness probe*) pour l'orchestrateur Docker.

#### `GET /metrics`

Point de collecte Prometheus automatisé par la bibliothèque `prometheus-fastapi-instrumentator`.

---

## 9. Services Partagés (`shared/`)

Les modules logés dans le répertoire `shared/` constituent la bibliothèque de composants communs réutilisés de manière transverse par les pipelines Kedro, l'API FastAPI et le tableau de bord Streamlit.

* **`shared/mongo.py` :** Encapsulation du client de connexion PyMongo. Fournit la méthode d'accès sécurisé aux collections de la base `bluesky_db`.
* **`shared/energy_service.py` :** Couche d'abstraction pour l'archivage et la récupération des journaux d'émissions carbone stockés dans la collection `energy_logs`.
* **`shared/finetuned_service.py` :** Singleton chargeant le modèle `xlm-roberta-base` fine-tuné depuis `data/06_models/xlm_roberta_finetuned/`. Classifieur **PRIMARY** de l'endpoint `/ask`. Lève `FileNotFoundError` si le dossier est absent (entraînement requis via `make run5`). Le chargement de `torch` et `transformers` est différé à l'instanciation pour éviter un import coûteux si le modèle n'existe pas.
* **`shared/embedding_service.py` :** Encodeur dense Singleton basé sur `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2` par défaut, configurable via `EMBEDDING_MODEL`). Produit des vecteurs L2-normalisés (384-dim). Expose également `extract_style_features(text)` (5 features stylistiques) et `ProbabilityScoreModel` (seuils de classification : 0.60 / 0.40 / 0.20).
* **`shared/reliability_service.py` :** Singleton chargeant le classifieur `LogisticRegression` sérialisé (`reliability_classifier.pkl`). Classifieur **FALLBACK 1** de l'endpoint `/ask`. Lève `FileNotFoundError` si l'artefact est absent (entraînement requis via `make run3`).
* **`shared/kmeans_service.py` :** Singleton chargeant l'artefact `kmeans_model.pkl`. Encode le texte via `embedding_service.encode()` (SentenceTransformer), puis prédit le cluster. Classifieur **FALLBACK 2** utilisé par `/ask` si `ReliabilityService` n'est pas disponible.
* **`shared/emotion_inference_service.py` :** Singleton chargeant le modèle `j-hartmann/emotion-english-distilroberta-base` via HuggingFace `pipeline`. Expose `classify(text)` qui retourne les 7 scores Ekman triés par confiance décroissante. Utilisé par l'endpoint `/emotion` et pré-chargé au démarrage de l'API.
* **`shared/ollama_service.py` :** Connecteur asynchrone gérant la communication avec l'API HTTP du conteneur Ollama local (`qwen2:1.5b`). Implémente `LLMInterface`. Inclut une détection automatique de la langue du texte soumis dans le prompt.
* **`shared/claude_service.py` :** Alternative d'explication LLM via `claude-agent-sdk` (modèle `claude-opus-4-6`). Implémente `LLMInterface`. Non actif en production principale (disponible comme remplacement d'Ollama).
* **`shared/gemini_service.py` :** Module redondant de secours s'appuyant sur le SDK officiel `google-genai` pour déporter l'analyse textuelle sur le cloud public en cas de surcharge des ressources locales.
* **`shared/rag.py` :** Moteur autonome de recherche par similarité cosinus s'appuyant sur un index pré-calculé (`rag_vectors.joblib`). Permet l'injection de contexte connexe au sein d'un prompt LLM (non actif sur l'API de production principale).
* **`shared/llm_interface.py` :** Classe abstraite pure définissant le contrat d'interface commun (`explain`) pour l'ensemble des intégrations de modèles de langage.
* **`shared/metrics.py` :** Déclaration centralisée des métriques Prometheus applicatives (`fakenews_verdict_total`, `fakenews_llm_latency_seconds`).

---

## 10. Interface Utilisateur (Streamlit)

L'IHM de restitution et d'interaction est déployée via Streamlit sur le port interne `8501`, puis exposée de manière publique sur le port standard HTTP `80` par le proxy inverse.

### Architecture fonctionnelle des sections

#### Onglet 1 : Fact-Check (Espace de dialogue interactif)

* Formulaire de saisie utilisateur de type chat (`st.chat_input`).
* À chaque soumission, deux requêtes sont lancées **en parallèle** via `concurrent.futures.ThreadPoolExecutor` :
  * `send_message_api(text)` → `POST /ask` (classification + explication LLM)
  * `analyze_message_emotion(text)` → `POST /emotion` (scores Ekman)
* Restitution du verdict : code couleur dynamique indexé sur la sévérité, jauge de confiance avec effet lumineux (*glow* CSS), explication LLM.
* **Analyse d'émotion intégrée (`render_emotion_chart`) :** Sous chaque réponse de l'assistant (et dans le replay de l'historique), un graphique en donut Altair affiche la répartition des 7 émotions, complété d'une rangée de badges colorés pour les émotions dépassant le seuil `probable` (0.40).
* Persistance locale de l'historique de discussion au sein de `st.session_state` (le champ `emotions` est stocké avec chaque message assistant pour le replay).

#### Onglet 2 : Analytics (Statistiques du corpus)

* Synthèse macroscopique du volume global de données via des cartes d'indicateurs (KPI Cards) : volume de posts, décompte d'auteurs uniques, diversité des thématiques.
* Restitution graphique animée via la bibliothèque Altair répartie sur quatre sous-sections :
* *Keywords :* Histogramme des 20 lemmes les plus fréquents (avec l'application d'une liste d'exclusion des mots vides (*stopwords*) français et anglais directement côté client).
* *Authors :* Diagrammes circulaires segmentés par catégorie décrivant la distribution des contributeurs les plus actifs (Palette de couleurs *Viridis*).
* *By Hour :* Graphique d'aire (*area chart*) de la distribution temporelle horaire des publications.
* *Emotions :* Analyse comparative de la répartition émotionnelle entre les posts Fake et Real, alimentée depuis la collection `emotion_posts` via les fonctions `emotion_distribution`, `emotion_by_category` et `avg_emotion_score`.


* Optimisation des performances via le décorateur de cache `@st.cache_data(ttl=300)`.

#### Onglet 3 : Energy Report (Bilan environnemental)

* Suivi précis des indicateurs d'éco-conception : somme globale de l'énergie électrique consommée (exprimée en Wh), masse équivalente de $CO_2$ émise (exprimée en mg), et identification du nœud algorithmique le plus énergivore.
* Visualisations Altair dédiées à la consommation : répartition de l'énergie par pipeline, consommation par nœud, décomposition fine de la puissance sollicitée (Proportion CPU vs RAM vs GPU) et historique chronologique des exécutions.

### Identité Visuelle et Thémisation

L'interface graphique adopte un design résolument moderne de type **dark glassmorphism** fortement inspiré des spécifications esthétiques de *visionOS* :

* **Arrière-plan :** Fond sombre (`#050510`), rehaussé par un effet d'aurore boréale mouvante généré en CSS pur à l'aide de quatre orbes lumineux animés via des cycles d'animation `@keyframes` asynchrones (périodes oscillant entre 20 et 38 secondes).
* **Composants graphiques (Cards) :** Conteneurs semi-transparents (`rgba(255,255,255,0.04)`) avec floutage d'arrière-plan (`backdrop-filter: blur(28px)`) et liseré de séparation subtil (`inset 0 1px 0 rgba(255,255,255,0.06)`).
* **Typographie & Éléments d'accentuation :** Intégration de la police de caractères *Inter* (via Google Fonts). Les éléments actifs utilisent la teinte violet électrique `#a78bfa`.

---

## 11. Reverse Proxy & Routage (Nginx)

L'accès à l'infrastructure s'effectue via un serveur HTTP Nginx configuré comme point d'entrée unique sur le port `80`. Sa configuration assure le routage inverse des requêtes ainsi que l'encapsulation des flux :

```
[Requête Utilisateur Port :80]
       │
       ├──► Route: /          ──► proxy_pass http://streamlit:8501 (Avec upgrade WebSocket)
       ├──► Route: /airflow/  ──► proxy_pass http://airflow-webserver:8080/airflow/
       ├──► Route: /grafana/  ──► proxy_pass http://grafana:3000
       └──► Route: /docs/     ──► proxy_pass http://docs/docs/  (Site MkDocs statique)

```

*Note d'infrastructure : Le serveur Streamlit s'appuyant nativement sur une communication bidirectionnelle permanente, le fichier de configuration `nginx.conf` surcharge explicitement les en-têtes HTTP de connexion afin d'autoriser l'élévation de protocole vers les sockets Web (`Upgrade $http_upgrade` ; `Connection: "upgrade"`).*

---

## 12. Observabilité & Monitoring (Prometheus & Grafana)

La surveillance de la santé du système et des performances d'inférence s'effectue via un écosystème de monitoring standardisé :

* **Prometheus :** Configuré pour interroger périodiquement (*scraping*) l'endpoint `/metrics` exposé par le service FastAPI ainsi que les données bas niveau du conteneur `node-exporter` (surveillance de la charge CPU, de la saturation RAM et des entrées/sorties disque de la machine hôte). Le conteneur `node-exporter` interagit directement avec le noyau Linux du serveur via le partage des répertoires systèmes `/proc` et `/sys` en mode `pid: host`.
* **Grafana :** Connecté à Prometheus comme source de données principale. Les tableaux de bord de supervision technique sont pré-provisionnés de manière automatique via des fichiers de configuration JSON localisés dans `conf/grafana/provisioning/`. L'authentification anonyme est activée en mode consultation (`GF_AUTH_ANONYMOUS_ENABLED=true`, rôle `Viewer`) pour faciliter le suivi.

---

## 13. Orchestration des Workflows (Apache Airflow)

La planification des tâches, la gestion des dépendances et la robustesse face aux pannes d'ingestion s'appuient sur un serveur **Apache Airflow 2.8.4** configuré avec l'exécuteur multinoyau `LocalExecutor`.

* **RDBMS de gestion d'état :** Base de données relationnelle MariaDB (`projet_etudes_db`).
* **Génération des graphes de tâches :** Transposition automatique des nœuds Kedro en tâches Airflow (*DAGs*) via l'extension de compilation `kedro-airflow`.

### Schedules et orchestration des DAGs

Les quatre DAGs du pipeline `__default__` forment une **chaîne de déclenchement** en cascade :

| DAG | Schedule autonome | Déclenchement |
| --- | --- | --- |
| `dag_ingest_from_bluesky` | `5 * * * *` — toutes les heures à H:05 | — |
| `dag_nlp_transform` | aucun | Déclenché par `ingest_from_bluesky` à sa fin |
| `dag_vectorisation` | `0 3 * * *` — filet de sécurité quotidien à 03:00 UTC | Déclenché aussi par `nlp_transform` |
| `dag_emotion_classification` | aucun | Déclenché par `nlp_transform` (en parallèle de `vectorisation`) |

Le flux nominal est donc : `ingest` (horaire) → `nlp_transform` → `vectorisation` + `emotion_classification` (en parallèle au niveau Airflow, chacun déclenché par `nlp_transform`).

### Processus d'initialisation de l'orchestrateur (Séquence de boot)

1. Le conteneur éphémère `airflow-init` temporise son démarrage en testant la disponibilité réseau du service `database` (jusqu'à 30 tentatives espacées de 5 secondes).
2. Exécution de la commande de migration de schéma `airflow db init` suivie de l'injection programmatique du compte d'administration principal (Identifiants par défaut : `admin` / `admin`).
3. Les services pivots `airflow-webserver` et `airflow-scheduler` valident leur condition de démarrage uniquement après l'arrêt complet avec succès du conteneur d'initialisation `airflow-init`.

---

## 14. Intégration et Déploiement Continus (CI/CD)

Les cycles de vérification du code et de déploiement s'appuient sur l'infrastructure GitHub Actions via le fichier de workflow `.github/workflows/ci.yml`.

```
[Événement Push (main, dev, develop, ci) / PR / Tag / workflow_dispatch]
       │
       ▼
Job [lint]
 ├── Validation syntaxique de style : ruff check (score plancher : 0 erreur)
 ├── Analyse de la qualité de programmation : pylint --fail-under=8.0
 ├── Validation des structures de configuration : yamllint
 └── Audit de conformité des couches de conteneurisation : hadolint (4 Dockerfiles)
       │
       ▼
Job [test] (Dépendant du succès de lint)
 ├── Extraction sécurisée des secrets GitHub (Variables d'environnement de test)
 └── Exécution des tests unitaires et d'intégration : pytest --cov
       │
       ▼
Job [deploy] (Dépendant du succès de test)
 Condition : tag Git (refs/tags/*) OU déclenchement manuel (workflow_dispatch)
 └── Connexion SSH sécurisée sur l'instance AWS EC2 cible
      ├── git pull origin main  ← toujours main (convention : les tags se posent sur main)
      ├── Reconstruction des images applicatives (docker compose build)
      └── Relance à chaud des conteneurs (docker compose up -d --pull never)

```

> **Convention de release :** Les tags de déploiement sont **toujours créés depuis `main`**. Le script SSH tire donc systématiquement `main`, quelle que soit la branche qui a déclenché le workflow. Poser un tag sur une autre branche sans merger vers `main` au préalable ne déploiera pas ce code.

---

## 15. Configuration & Variables d'Environnement

L'ensemble des secrets et des paramètres d'infrastructure est centralisé au sein d'un fichier isolé `.env`, exclu du versionnage de code et injecté dynamiquement dans les conteneurs Docker au runtime.

| Clef de configuration | Périmètre d'impact | Rôle / Description technique |
| --- | --- | --- |
| `MONGO_CONNECTION_STRING` | Global | Chaîne d'authentification NoSQL (`mongodb://user:pass@host:port/`) |
| `BSKY_USERNAME` | Ingestion | Identifiant de compte (handle) pour l'accès à l'API Bluesky |
| `BSKY_APP_PASSWORD` | Ingestion | Jeton d'application spécifique (*App Password*) généré sur Bluesky |
| `OLLAMA_HOST` | API Applicative | Point d'accès réseau vers l'API d'Ollama (`http://ollama:11434`) |
| `OLLAMA_MODEL` | API Applicative | Modèle LLM cible. Forcé à `qwen2:1.5b` dans `docker-compose.yml` ; le code `ollama_service.py` default à `llama3.2:3b` si la variable est absente. |
| `EMBEDDING_MODEL` | API / Pipeline | Modèle SentenceTransformer pour `ReliabilityService` et `train_reliability`. Optionnel — default : `paraphrase-multilingual-MiniLM-L12-v2`. |
| `API_URL` | Interface Web | Point d'accès réseau vers le service FastAPI (`http://api:8080/`) |
| `GOOGLE_API_KEY` | Module Failover | Clé d'authentification pour le service distant de secours Gemini |
| `ANTHROPIC_API_KEY` | Module Failover | Clé d'authentification pour `ClaudeService` (`claude-agent-sdk`). Non requis si `ClaudeService` n'est pas activé (non câblé en production par défaut). |

---

## 16. Cycle de Vie de la Donnée & Flux de Bout en Bout

Le diagramme de séquence ci-dessous détaille le cheminement complet de l'information au sein du système, depuis la scrutation des serveurs de Bluesky par l'orchestrateur jusqu'à l'accès en temps réel par l'utilisateur final.

```mermaid
sequenceDiagram
    participant AF as Airflow Scheduler
    participant KD as Kedro + EnergyHook
    participant BS as API Distante Bluesky
    participant MG as MongoDB Atlas
    participant API as FastAPI (:8080)
    participant OL as Serveur Ollama
    participant ST as Serveur Streamlit
    actor User as Utilisateur Final

    rect rgb(25, 35, 65)
        Note over AF,MG: Étape 1 : Ingestion horaire (H:05)
        AF->>KD: kedro run --pipeline=ingest_from_bluesky
        KD->>BS: search_posts(keyword, limit=25) sur 20 axes thématiques
        BS-->>KD: Payloads JSON bruts
        KD->>MG: insert_many ──► Collection: posts
        KD->>MG: Télémétrie ──► Collection: energy_logs
    end

    rect rgb(25, 55, 60)
        Note over AF,MG: Étape 2 : NLP (déclenché par ingest)
        AF->>KD: kedro run --pipeline=nlp_transform
        KD->>MG: Requête différentielle (unique_id absents de cleaned_posts)
        MG-->>KD: Textes bruts non traités
        KD->>KD: clean_text() + normalize_text()
        KD->>MG: Upsert ──► Collection: cleaned_posts
        KD->>MG: Télémétrie ──► Collection: energy_logs
    end

    rect rgb(25, 65, 40)
        Note over AF,MG: Étape 3a : Vectorisation (déclenché par nlp_transform ou quotidien 03:00 UTC)
        AF->>KD: kedro run --pipeline=vectorisation
        KD->>MG: Textes nettoyés non classifiés
        MG-->>KD: Corpus normalisé
        KD->>KD: SentenceTransformer (embeddings) + KMeans (k=2) ──► labels is_real (orientation dynamique)
        KD->>MG: bulk_write ──► Collection: classified_posts
        KD->>KD: Export : kmeans_model.pkl / reliability_classifier.pkl
        KD->>MG: Télémétrie ──► Collection: energy_logs
    end

    rect rgb(20, 60, 50)
        Note over AF,MG: Étape 3b : Émotion (déclenché par nlp_transform, en parallèle de 3a)
        AF->>KD: kedro run --pipeline=emotion_classification
        KD->>MG: Textes nettoyés non encore classifiés en émotion
        MG-->>KD: Corpus normalisé (incrémental)
        KD->>KD: DistilRoBERTa (j-hartmann) ──► émotion dominante + score
        KD->>MG: bulk_write ──► Collection: emotion_posts
        KD->>MG: Télémétrie ──► Collection: energy_logs
    end

    rect rgb(65, 25, 30)
        Note over User,ST: Étape 4 : Inférence temps réel
        User->>ST: Soumission d'une affirmation (Onglet Fact-Check)
        par Appels parallèles (ThreadPoolExecutor)
            ST->>API: POST /ask {"question": "..."}
            API->>API: ReliabilityService (LogisticRegression + embeddings) — repli KMeans si pkl absent
            API->>OL: POST /api/chat (qwen2:1.5b) — explication stylistique
            OL-->>API: Explication en langage naturel
            API-->>ST: {verdict, probability, based_on, explanation}
        and
            ST->>API: POST /emotion {"text": "..."}
            API->>API: EmotionInferenceService (DistilRoBERTa) ──► 7 scores Ekman
            API-->>ST: {emotions: [...]}
        end
        ST-->>User: Verdict coloré + jauge + explication LLM + donut émotions
    end

```

---

## 17. Guide de Démarrage Rapide

### Prérequis Système

* Moteur Docker et extension Docker Compose v2.
* Fichier d'environnement `.env` dûment configuré à la racine du projet (voir §15).
* **RAM disponible recommandée : ≥ 6 Go.** Ollama (`qwen2:1.5b` ~900 Mo), DistilRoBERTa (~300 Mo) et SentenceTransformer (~120 Mo) coexistent dans le conteneur `api` au démarrage.
* Connexion Internet lors de la première construction : téléchargement cumulé d'environ **2–3 Go** (images Docker de base + modèle Ollama + modèles HuggingFace). Les runs suivants utilisent les volumes `ollama-data` et `hf-cache`.

### Déploiement en Environnement de Production (Hôte Linux)

L'intégration sur le serveur s'effectue automatiquement via la CI/CD lors de la création d'un **tag Git sur `main`** ou d'un déclenchement manuel (`workflow_dispatch`). Pour forcer manuellement une réinitialisation à chaud directement sur le serveur :

```bash
# Accès au répertoire applicatif sur l'instance cloud
cd ~/projet_etudes_data

# Synchronisation du dépôt local avec le serveur de référence
git pull origin main

# Reconstruction globale des images de conteneurs sans cache corrompu
docker compose build

# Instanciation de la stack applicative en tâche de fond
docker compose up -d --pull never

```

L'ensemble de l'écosystème devient immédiatement accessible via les adresses de routage suivantes :

* **Interface Applicative principale (Streamlit) :** `http://<EC2_PUBLIC_IP>/`
* **Console d'Administration des flux (Airflow UI) :** `http://<EC2_PUBLIC_IP>/airflow/`
* **Tableaux de bord de supervision (Grafana) :** `http://<EC2_PUBLIC_IP>/grafana/`

### Déploiement en Environnement de Développement Local

Pour instancier rapidement l'ensemble de l'infrastructure au sein d'un environnement Docker local :

```bash
make up
# Enchaîne trois étapes :
#   1. docker compose build --no-cache  (reconstruction des images)
#   2. airflow-init                     (migration BD Airflow + création du compte admin)
#   3. docker compose up -d             (démarrage de tous les services)

```

L'interface utilisateur devient accessible localement sur l'adresse de bouclage standard : `http://localhost/`.

### Exécution Manuelle et Séquentielle des Pipelines Data

Dans le cadre de tests ou d'une initialisation manuelle pas à pas du projet, l'arbre de dépendance technique impose le respect strict de l'ordre d'exécution suivant sous peine de blocage de l'API par manque d'artefacts :

```bash
# Étape 1 : Initialisation de l'environnement virtuel et installation des dépendances
make install-all   # uv sync --extra dev

# Étape 2 : Activation du flux d'ingestion réseau depuis l'API Bluesky
make run1          # kedro run --pipeline=ingest_from_bluesky

# Étape 3 : Lancement du nettoyage textuel et des transformations NLP
make run2          # kedro run --pipeline=nlp_transform

# Étape 4 : Vectorisation + entraînement du classifieur de fiabilité (enchaînés par make run3)
#   Sans cette étape, l'API démarre en mode dégradé (repli KMeans).
make run3
# Équivalent à :
#   kedro run --pipeline=vectorisation
#   kedro run --pipeline=train_reliability

# Étape 5 : Classification des émotions (optionnel pour le démarrage de l'API,
#   requis pour alimenter l'onglet Analytics > Emotions de Streamlit)
make run4          # kedro run --pipeline=emotion_classification

# Étape 6 (optionnel) : Fine-tuning xlm-roberta (activer le classifieur PRIMARY)
#   Nécessite un corpus suffisant (≥ 30 posts reliable + ≥ 30 Misinformation).
#   CPU-only : plusieurs heures. Avec GPU : ~15-30 min.
make run5          # kedro run --pipeline=train_finetuned

# Alternative : exécuter toutes les étapes 1-5 en séquence
make runall        # run1 → run2 → run3 → run4 → run5

# Étape 7 : Démarrage des modules applicatifs de service
make api           # uvicorn src.api.api:app --host 0.0.0.0 --port 8080
make web           # streamlit run src/streamlit_app/streamlit_app.py

```

### Extinction de l'Infrastructure

Pour interrompre la totalité des services conteneurisés et purger les volumes éphémères associés :

```bash
make down          # docker compose down -v

```

---

## 18. Limitations Connues & Dette Technique

| # | Limitation | Impact | Piste d'amélioration |
| --- | --- | --- | --- |
| 1 | **Labels terrain partiels** : `train_reliability` est entraîné uniquement sur les posts `source_label = "reliable"` (comptes vérifiés) et les posts de catégorie `"Misinformation"` — le reste du corpus (`"unverified"`) n'est pas labellisé. Le classifieur n'est entraîné que sur une sous-population potentiellement non représentative. | La généralisation sur les posts `"unverified"` n'est pas garantie. | Annoter manuellement un échantillon du corpus `"unverified"`, ou enrichir la liste `reliable_domains`. |
| 2 | **Modèle d'émotion anglophone** : `j-hartmann/emotion-english-distilroberta-base` est entraîné sur de l'anglais. Bluesky contient des posts multilingues. | Scores d'émotion potentiellement inexacts sur les posts non anglais. | Utiliser un modèle multilingue ou filtrer l'ingestion à `lang="en"` uniquement. |
| 3 | **HTTP sans TLS** : Nginx expose uniquement le port 80. Les communications sont en clair. | Pas de confidentialité des données en transit, pas d'URL `https://`. | Mettre en place Let's Encrypt + Certbot ou un reverse proxy TLS en amont (Cloudflare, Caddy). |
| 4 | **Credentials Airflow par défaut** : `admin`/`admin` et `AIRFLOW__WEBSERVER__SECRET_KEY=changeme` sont codés dans `docker-compose.yml`. | Exposition de l'interface Airflow à toute personne connaissant l'IP du serveur. | Injecter ces valeurs via le fichier `.env` et forcer leur changement au premier déploiement. |
| 5 | **Indexation MongoDB partielle** : `MongoIndexHook` crée un index non-unique sur `unique_id` (toutes collections), mais aucun index sur `created_at`, `category` ou `classified_at`. | Requêtes filtrées sur ces champs de plus en plus lentes sur les grands corpus. | Ajouter des index composés sur les champs de filtrage fréquents ; envisager un TTL sur `classified_posts` pour limiter la taille. |
| 6 | **Inférence Ollama CPU-only** : Le modèle `qwen2:1.5b` tourne sur CPU dans Docker. | Latence de réponse `/ask` pouvant atteindre 2–3 minutes à froid (premier appel après démarrage). | Passer à une instance avec GPU ou utiliser `ClaudeService` / `GeminiService` comme fallback LLM. |
| 7 | **`rag.py`, `claude_service.py`, `gemini_service.py`** : Modules présents dans `shared/` mais non câblés à l'API de production. | Code mort maintenu, risque de divergence silencieuse avec l'API active. | Soit intégrer formellement, soit déplacer dans un répertoire `experimental/` clairement séparé. |
| 8 | **Fine-tuning CPU-only** : `train_finetuned` (run5) ne détecte pas de GPU dans les environnements EC2 standard. | Plusieurs heures d'entraînement pour 3 epochs sur un corpus modeste. | Utiliser une instance EC2 avec GPU (p3/g4dn) pour le run5, ou entraîner localement puis copier `data/06_models/xlm_roberta_finetuned/` sur le serveur. |
| 9 | **Modèle fine-tuné non entraîné par défaut** : `data/06_models/xlm_roberta_finetuned/` est absent au premier déploiement. | L'API démarre en mode dégradé (ReliabilityService ou KMeans). Le classifieur PRIMARY xlm-roberta est inactif. | Exécuter `make run5` après constitution d'un corpus suffisant (≥ 30 posts par classe). |
