# Document d'Architecture Technique (DAT) — Projet d'études M1 Data

**Projet :** M1 Data Science — Plateforme de détection automatisée d'infox (*fake news*) sur le réseau Bluesky

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
    - [Mécanismes de Persistance (Volumes)](#mécanismes-de-persistance-volumes)
    - [Gestion de la Santé des Services (Healthchecks)](#gestion-de-la-santé-des-services-healthchecks)
  - [5. Pipelines de Données (Framework Kedro)](#5-pipelines-de-données-framework-kedro)
    - [5.1 Pipeline `ingest_from_bluesky`](#51-pipeline-ingest_from_bluesky)
      - [Algorithme d'ingestion](#algorithme-dingestion)
    - [5.2 Pipeline `nlp_transform`](#52-pipeline-nlp_transform)
      - [Logique de nettoyage incrémental](#logique-de-nettoyage-incrémental)
    - [5.3 Pipeline `vectorisation`](#53-pipeline-vectorisation)
      - [Mécanisme mathématique et clustering](#mécanisme-mathématique-et-clustering)
    - [5.4 Pipeline `model_training` (Exécution Asynchrone / Ponctuelle)](#54-pipeline-model_training-exécution-asynchrone--ponctuelle)
      - [Architecture logique du réseau de neurones](#architecture-logique-du-réseau-de-neurones)
    - [5.5 Pipeline `emotion_classification`](#55-pipeline-emotion_classification)
    - [5.6 Pipeline `train_reliability` (Exécution Asynchrone / Ponctuelle)](#56-pipeline-train_reliability-exécution-asynchrone--ponctuelle)
  - [6. Couche de Persistance (MongoDB)](#6-couche-de-persistance-mongodb)
    - [Schéma logique des collections](#schéma-logique-des-collections)
  - [7. Green IT \& Monitoring Énergétique (EnergyHook)](#7-green-it--monitoring-énergétique-energyhook)
  - [8. Couche Applicative \& API de Classification (FastAPI)](#8-couche-applicative--api-de-classification-fastapi)
    - [Spécification des Points d'Accès (Endpoints)](#spécification-des-points-daccès-endpoints)
      - [`POST /ask`](#post-ask)
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
    - [Processus d'initialisation de l'orchestrateur (Séquence de boot)](#processus-dinitialisation-de-lorchestrateur-séquence-de-boot)
  - [14. Intégration et Déploiement Continus (CI/CD)](#14-intégration-et-déploiement-continus-cicd)
  - [15. Configuration \& Variables d'Environnement](#15-configuration--variables-denvironnement)
  - [16. Cycle de Vie de la Donnée \& Flux de Bout en Bout](#16-cycle-de-vie-de-la-donnée--flux-de-bout-en-bout)
  - [17. Guide de Démarrage Rapide](#17-guide-de-démarrage-rapide)
    - [Prérequis Système](#prérequis-système)
    - [Déploiement en Environnement de Production (AWS EC2)](#déploiement-en-environnement-de-production-aws-ec2)
    - [Déploiement en Environnement de Développement Local](#déploiement-en-environnement-de-développement-local)
    - [Exécution Manuelle et Séquentielle des Pipelines Data](#exécution-manuelle-et-séquentielle-des-pipelines-data)
    - [Extinction de l'Infrastructure](#extinction-de-linfrastructure)

---

## 1. Vue d'ensemble & Architecture Générale

**FakeShield** est une plateforme industrialisée de détection et d'analyse des fausses informations circulant sur le réseau social décentralisé **Bluesky**. Le système s'articule autour de quatre pipelines de données managés, d'une API de classification en temps réel et d'un tableau de bord décisionnel.

L'écosystème respecte un paradigme architectural linéaire **ETL → ML → API → UI** :


```

Bluesky API
│  atproto (Recherche par mots-clés)
▼
MongoDB [Collection: posts]
│  Kedro nlp_transform
▼
MongoDB [Collection: cleaned_posts]
│  Kedro vectorisation + emotion_classification (en parallèle dans __default__)
▼
MongoDB [Collection: classified_posts]   MongoDB [Collection: emotion_posts]
Artefacts (ReliabilityClassifier + TF-IDF/KMeans) ──► FastAPI (/ask, /emotion) ◄── Streamlit UI
│
Ollama LLM  (Interprétabilité NLP)
```

---

## 2. Structure du Dépôt

```
projet_etudes_data/
├── conf/
│   ├── base/
│   │   ├── catalog.yml                  # Catalogue des Datasets Kedro
│   │   ├── parameters.yml               # Paramètres globaux
│   │   ├── parameters_ingest_from_bluesky.yml
│   │   ├── parameters_nlp_transform.yml
│   │   ├── parameters_vectorisation.yml  # Hyperparamètres (clusters, features, artefacts)
│   │   └── parameters_model_training.yml # Configuration du réseau de neurones LSTM
│   ├── airflow/                          # Configuration cible pour l'environnement Airflow
│   ├── nginx.conf                        # Configuration du Reverse Proxy
│   ├── prometheus.yml                    # Configuration du serveur de métriques
│   └── logging.yml                       # Stratégie de journalisation
├── data/
│   ├── 01_raw/                           # Sources Kaggle (True.csv, Fake.csv - non versionnés)
│   └── 06_models/                        # Sérialisation des modèles (Pickle & Keras)
├── dags/                                 # DAGs Airflow auto-générés par kedro-airflow
├── shared/                               # Composants transverses partagés (API, UI, Pipelines)
│   ├── mongo.py                          # Connecteur de persistance
│   ├── energy_service.py                 # Gestionnaire des métriques CodeCarbon
│   ├── kmeans_service.py                 # Moteur d'inférence KMeans (fallback)
│   ├── reliability_service.py            # Classifieur supervisé principal (LogisticRegression + embeddings)
│   ├── embedding_service.py              # Encodage SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2)
│   ├── emotion_inference_service.py      # Classifieur d'émotions temps-réel (DistilRoBERTa)
│   ├── ollama_service.py                 # Client d'inférence LLM local
│   ├── claude_service.py                 # Client d'inférence Claude (claude-agent-sdk)
│   ├── gemini_service.py                 # Solution LLM Cloud redondante
│   ├── lstm_service.py                   # Service d'inférence supervisé (Deep Learning)
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
│   └── streamlit_app/
│       ├── streamlit_app.py              # Point d'entrée IHM (incl. render_emotion_chart)
│       ├── streamlit_logic.py            # Logique de présentation & requêtage (incl. analyze_message_emotion)
│       ├── streamlit_color_chart.py      # Thémisation graphique
│       ├── streamlit_config.py           # Configuration de l'IHM
│       └── config.toml                   # Paramètres natifs Streamlit
├── Dockerfile.api
├── Dockerfile.airflow
├── Dockerfile.streamlit
├── docker-compose.yml
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
| **Machine Learning** | scikit-learn | ~1.5.1 | Extraction de features (TF-IDF) et clustering (KMeans) |
| **Deep Learning** | TensorFlow / Keras | *latest* | Entraînement du modèle de référence LSTM |
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
| **Green IT** | CodeCarbon | *latest* | Évaluation des émissions de $CO_2$ et de la puissance consommée |
| **Collecte Métriques** | Prometheus | *latest* | Base de données temporelle pour le monitoring technique |
| **Orchestration Workflow** | Apache Airflow | 2.8.4 | Ordonnancement et supervision des tâches ETL |
| **Serveur Frontal / Proxy** | Nginx | *alpine* | Reverse proxy, gestion des certificats et routage HTTP |
| **RDBMS Airflow** | MariaDB | *latest* | Base de données de gestion d'états pour Airflow |
| **Conteneurisation** | Docker / Compose | v2 | Isolation et portabilité de la stack applicative |
| **Qualité Code** | Black / Ruff | *latest* / ~0.12.0 | Formater, linter et garantir la conformité du code source |
| **Sécurité DevOps** | `hadolint` / Trivy | v3.1.0 / *latest* | Audit de sécurité des conteneurs et des dépendances |
| **Tests** | pytest / pytest-cov | ~7.2 | Automatisation des tests et couverture de code |

---

## 4. Infrastructure & Conteneurisation (Docker)

### Environnement de Production

L'application est déployée sur une instance cloud **AWS EC2 (Amazon Linux 2023)** managée via **Docker Compose v2**. L'intégration est entièrement automatisée : tout déploiement est instancié suite à la validation du pipeline CI/CD lors d'un événement `push` sur la branche `main`.

L'écosystème applicatif est segmenté en micro-services isolés :

| Service Docker | Source d'Image | Port Hôte | Port Conteneur | Responsabilité Métier |
| --- | --- | --- | --- | --- |
| `nginx` | `nginx:alpine` | 80 | 80 | Point d'entrée unique du trafic (Reverse Proxy) |
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
                   └──► airflow-webserver
streamlit ─────────────► api (Statut de santé requis)
api ────────────────────► ollama (Statut de santé requis)
airflow-webserver ──────► airflow-init (Statut: success requis)
airflow-scheduler ──────► airflow-init (Statut: success requis)
airflow-init ───────────► database

```

### Mécanismes de Persistance (Volumes)

* `airflow-logs` & `airflow-plugins` : Conservation des journaux applicatifs et extensions d'orchestration.
* `ollama-data` : Persistance locale des poids du modèle LLM (`qwen2:1.5b`), évitant les téléchargements redondants au démarrage.
* `hf-cache` : Cache des modèles HuggingFace (`~/.cache/huggingface`) partagé entre les redéploiements du conteneur `api`. Évite le re-téléchargement du modèle DistilRoBERTa d'émotion à chaque build.
* `./data` (Volume lié à l'hôte) : Monté au sein du conteneur `api` pour assurer l'accès aux modèles sérialisés par Kedro (`.pkl`).

### Gestion de la Santé des Services (Healthchecks)

Le service `ollama` implémente une routine de démarrage robuste. Il instancie le démon `ollama serve` puis orchestre le téléchargement du modèle via `ollama pull qwen2:1.5b` (Volume d'environ 900 Mo). La sonde de santé vérifie périodiquement la disponibilité du modèle via la commande `ollama list | grep qwen2`, s'accordant un délai maximal de 300 secondes (20 tentatives d'intervalle).

Le service `api` dispose d'un `start_period` porté à **60 secondes** (contre 15 précédemment) afin de laisser le temps au mécanisme de lifespan FastAPI de pré-charger le modèle d'émotion DistilRoBERTa avant que les sondes de santé ne soient déclarées actives.

---

## 5. Pipelines de Données (Framework Kedro)

Le framework **Kedro 1.0.0** est utilisé comme colonne vertébrale pour structurer le code de traitement de données. Les modules sont partitionnés en quatre pipelines distincts au sein de `pipeline_registry.py`.

Par défaut, le pipeline `__default__` exécute le cycle ETL complet :


$$\text{ingest\_from\_bluesky} \longrightarrow \text{nlp\_transform} \longrightarrow \text{vectorisation} \longrightarrow \text{emotion\_classification}$$

Le pipeline `model_training` est isolé volontairement de la routine par défaut. Il s'agit d'une brique d'entraînement supervisé lourd s'appuyant sur des données externes historiques (Kaggle).

Le pipeline `train_reliability` est également isolé : il doit être exécuté une première fois pour générer `reliability_classifier.pkl` avant que l'API puisse utiliser le classifieur supervisé.

```mermaid
flowchart LR
    BS(["🌐 API Bluesky"])
    M1[("MongoDB\nposts")]
    M2[("MongoDB\ncleaned_posts")]
    M3[("MongoDB\nclassified_posts")]
    M4[("MongoDB\nemotion_posts")]
    PKL[("data/06_models/\n*.pkl")]

    subgraph P1["Pipeline : ingest_from_bluesky"]
        N1["fetch_from_keywords"]
        N2["save_posts_to_db"]
        N1 --> N2
    end

    subgraph P2["Pipeline : nlp_transform"]
        N3["get_posts_to_treat"]
        N4["clean_text"]
        N5["normalize_text"]
        N6["save_to_db"]
        N3 --> N4 --> N5 --> N6
    end

    subgraph P3["Pipeline : vectorisation"]
        N7["get_cleaned_posts"]
        N8["vectorize_texts\nTF-IDF (5k Features)"]
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

    BS --> N1
    N2 --> M1
    M1 --> N3
    N6 --> M2
    M2 --> N7
    M2 --> N12
    N10 --> PKL
    N11 --> M3
    N14 --> M4

```

### 5.1 Pipeline `ingest_from_bluesky`

* **Objectif :** Collecter de manière ciblée les publications du réseau décentralisé Bluesky et assurer leur persistance brute.
* **Composants (Nodes) :**
* `fetch_from_keywords_node` : Interroge l'API distante.
* `save_posts_to_db_node` : Insère les données récupérées en base de données.



#### Algorithme d'ingestion

1. **Authentification :** Connexion via la bibliothèque `atproto.Client.login()` en exploitant les variables d'environnement `BSKY_USERNAME` et `BSKY_APP_PASSWORD`.
2. **Stratégie d'exploration :** Requêtage structuré autour de quatre axes thématiques :
* *Discover :* `news`, `world news`, `science`, `technology`, `research`
* *Trending :* `breaking news`, `urgent`, `live updates`, `alert`
* *Hot Topics :* `politics`, `election`, `climate`, `crisis`, `economy`, `AI`
* *Misinformation :* `fact check`, `debunked`, `misinformation`, `conspiracy`, `hoax`


3. **Exécution :** Appel de la méthode `app.bsky.feed.search_posts(q=keyword, limit=25, lang="en")` pour chaque mot-clé.
4. **Déduplication & Intégrité :** Génération d'un identifiant composite unique défini par le motif `{username}_{created_at}`. Le script écarte systématiquement les doublons intra-requête à l'aide d'une structure `seen_uris` et filtre les publications corrompues dépourvues de contenu textuel ou de métadonnées temporelles.
5. **Persistance brute :** Opération d'écriture groupée (`insert_many`) au sein de la collection `posts`.

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

* **Commande d'activation :** `kedro run --pipeline=nlp_transform` (ou via `make run2`).

---

### 5.3 Pipeline `vectorisation`

* **Objectif :** Transformer le texte nettoyé en représentations numériques, segmenter le corpus via un algorithme non supervisé, et exporter les modèles entraînés pour l'IHM et l'API.
* **Configuration de référence (`conf/base/parameters_vectorisation.yml`) :**
```yaml
vectorisation:
  n_clusters: 2
  max_features: 5000
  vectorizer_path: "data/06_models/tfidf_vectorizer.pkl"
  kmeans_path:     "data/06_models/kmeans_model.pkl"

```



#### Mécanisme mathématique et clustering

Le pipeline extrait le texte normalisé des publications non traitées. Les chaînes de caractères subissent une transformation vectorielle de type **TF-IDF (Term Frequency-Inverse Document Frequency)** restreinte aux $5000$ descripteurs les plus pertinents, avec l'application d'un lissage logarithmique de la fréquence des termes (`sublinear_tf=True`).

La matrice résultante $X$ est soumise à un partitionnement via l'algorithme des **K-Means** ($k=2$).

> **Règle métier de labellisation :**
> * **Cluster 1** $\longrightarrow$ Postulat Légitime (`is_real = True`)
> * **Cluster 0** $\longrightarrow$ Anomalie / Infox potentielle (`is_real = False`)
>
>

Le score de confiance est déterminé à partir du calcul du ratio des distances euclidiennes par rapport aux centres de gravité (*centroïdes*) des deux clusters :

$$\text{Score} = \frac{d(\mathbf{x}, \mathbf{c}_0)}{d(\mathbf{x}, \mathbf{c}_0) + d(\mathbf{x}, \mathbf{c}_1) + \varepsilon}$$

*Où $\mathbf{x}$ représente le vecteur du post, $\mathbf{c}_0$ le centroïde du cluster "Fake", $\mathbf{c}_1$ le centroïde du cluster "Real", et $\varepsilon = 10^{-8}$ une constante de stabilité numérique.* Un score élevé indique une forte probabilité de véracité de l'information.

Les artefacts entraînés sont sérialisés au format Pickle dans `data/06_models/` tandis que les résultats d'inférence font l'objet d'un import de masse transactionnel (`bulk_write` avec des opérations `UpdateOne` et `upsert=True`) dans la collection `classified_posts`.

* **Commande d'activation :** `kedro run --pipeline=vectorisation` (ou via `make run3`).

---

### 5.4 Pipeline `model_training` (Exécution Asynchrone / Ponctuelle)

* **Objectif :** Entraîner à des fins comparatives un classifieur deep learning de type LSTM (*Long Short-Term Memory*) sur le jeu de données de référence Kaggle *« Fake and Real News »*.
* **Hyperparamètres du réseau (`conf/base/parameters_model_training.yml`) :**
```yaml
model_training:
  vocab_size:    5000
  max_len:       200
  embedding_dim: 128
  epochs:        10
  batch_size:    64
  model_path:     "data/06_models/lstm_model.keras"
  tokenizer_path: "data/06_models/lstm_tokenizer.pkl"

```



#### Architecture logique du réseau de neurones

Le dataset d'entraînement fusionne les sources `True.csv` et `Fake.csv`. Le texte est tokenisé et harmonisé à une longueur fixe de $200$ jetons (complétion par *post-padding*). La topologie du réseau Keras est configurée ainsi :

```
Couche d'Entrée : Embedding (Vocabulaire: 5000, Dimension: 128, Séquence: 200)
       │
       ▼
Couche Récurrente : LSTM (128 Unités, return_sequences=True)
       │
       ▼
Régularisation : Dropout (Taux de désactivation: 0.5)
       │
       ▼
Couche Récurrente : LSTM (64 Unités)
       │
       ▼
Régularisation : Dropout (Taux de désactivation: 0.5)
       │
       ▼
Couche Dense Intermédiaire : Neurones: 32 | Activation: ReLU
       │
       ▼
Couche de Sortie Classifieur : Neurones: 1 | Activation: Sigmoïde

```

L'optimisation repose sur l'algorithme Adam conjugué à une fonction de perte d'entropie croisée binaire (*binary crossentropy*). Un mécanisme d'arrêt précoce (*EarlyStopping*) surveille la métrique `val_accuracy` avec une tolérance de 3 époques afin de restituer les meilleurs poids et d'éviter le surapprentissage.

* **Commande d'activation :** `kedro run --pipeline=model_training`.

---

### 5.5 Pipeline `emotion_classification`

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

### 5.6 Pipeline `train_reliability` (Exécution Asynchrone / Ponctuelle)

* **Objectif :** Entraîner un classifieur de fiabilité supervisé sur le corpus Bluesky classé, qui devient le **classifieur principal** exposé par l'API (remplaçant KMeans).
* **Architecture :**
  1. Extraction de `classified_posts` (champ `is_real` comme label, `normalized_text` comme feature).
  2. Encodage dense via `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2`) — vecteurs L2-normalisés.
  3. Entraînement d'une `LogisticRegression` (scikit-learn) avec `class_weight="balanced"` et validation croisée ROC-AUC (5-fold).
  4. Sérialisation du classifieur dans `data/06_models/reliability_classifier.pkl`.

Le score ROC-AUC est journalisé à l'issue de l'entraînement. Ce pipeline doit être exécuté au moins une fois avant le démarrage de l'API pour activer la voie d'inférence principale.

* **Commande d'activation :** `kedro run --pipeline=train_reliability`.

---

## 6. Couche de Persistance (MongoDB)

L'application centralise ses données au sein d'une instance NoSQL MongoDB unique nommée `bluesky_db`. Les accès clients sont initialisés par le module partagé `shared/mongo.py` à l'aide de l'URI de connexion injectée via la variable d'environnement `MONGO_CONNECTION_STRING`.

### Schéma logique des collections

```
bluesky_db (Base de données)
  ├── posts (Publications brutes)
  │     └── [ _id, unique_id, username, text, created_at, category, utc_saved_at ]
  │
  ├── cleaned_posts (Publications prétraitées par NLP)
  │     └── [ _id, unique_id, username, created_at, category, normalized_text, utc_saved_at ]
  │
  ├── classified_posts (Résultats d'inférence KMeans/Reliability)
  │     └── [ _id, unique_id, username, category, normalized_text, fake_news_prob, is_real, cluster, classified_at ]
  │
  ├── emotion_posts (Résultats d'inférence DistilRoBERTa — Ekman 7)
  │     └── [ _id, unique_id, username, category, normalized_text, emotion, emotion_score, classified_at ]
  │
  └── energy_logs (Traces de consommation CodeCarbon)
        └── [ _id, pipeline_name, node_name, run_id, timestamp, duration_s, energy_kwh, co2_kg, ... ]

```

---

## 7. Green IT & Monitoring Énergétique (EnergyHook)

Afin d'intégrer les problématiques d'éco-conception logicielle (Green IT), le projet intègre un mécanisme d'audit énergétique systématique via l'implémentation de la classe `EnergyHook` (située dans `src/projet_etudes/hooks.py`), qui étend le cycle de vie natif de Kedro.

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
       │  Appel asynchrone à energy_service.save_energy_log()
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

Prend en charge l'évaluation instantanée d'une affirmation soumise par un utilisateur.

* **Contrat d'entrée (JSON) :**
```json
{ "question": "L'affirmation textuelle à analyser" }
```

* **Logique métier interne :**
1. **Phase de classification synchrone (ReliabilityService — principal) :** Encodage du texte via `SentenceTransformer` puis prédiction de probabilité par `LogisticRegression`. Si le fichier `reliability_classifier.pkl` est absent, repli automatique sur `KMeansService` avec journalisation d'un avertissement.
2. **Traduction du score en verdict discret (`ProbabilityScoreModel`) :**
   * $\text{Score} \ge 0.60 \longrightarrow \text{"true"}$
   * $\text{Score} \ge 0.40 \longrightarrow \text{"very likely true"}$
   * $\text{Score} \ge 0.20 \longrightarrow \text{"uncertain"}$
   * $\text{Score} > 0 \longrightarrow \text{"very likely false"}$
   * $\text{Score} = 0 \longrightarrow \text{"false"}$
3. **Phase d'explication asynchrone (`OllamaService`) :** Sollicitation du LLM local `qwen2:1.5b` par une requête HTTP asynchrone (`httpx.AsyncClient`) avec un timeout de 300 secondes. Le prompt détecte la langue du texte soumis et répond dans cette même langue, se limitant à 2-3 phrases sur les caractéristiques stylistiques du texte. En cas de défaillance d'Ollama, une chaîne vide est retournée sans bloquer la réponse de classification.
4. **Télémétrie :** Incrémentation des compteurs Prometheus selon le verdict rendu.

* **Contrat de sortie (JSON) :**
```json
{
  "verdict": "true | very likely true | uncertain | very likely false | false",
  "probability": 0.9124,
  "based_on": "reliability_classifier",
  "explanation": "L'analyse linguistique met en évidence une structure syntaxique informative dénuée d'artifices hyperboliques..."
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
* **`shared/embedding_service.py` :** Encodeur dense Singleton basé sur `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2` par défaut, configurable via `EMBEDDING_MODEL`). Produit des vecteurs L2-normalisés. Partagé par `ReliabilityService` et le pipeline `train_reliability`. Expose également `ProbabilityScoreModel` (seuils de classification : 0.60 / 0.40 / 0.20).
* **`shared/reliability_service.py` :** Singleton chargeant le classifieur `LogisticRegression` sérialisé (`reliability_classifier.pkl`). Classifieur **principal** de l'endpoint `/ask`. Lève `FileNotFoundError` si l'artefact est absent (entraînement requis via `train_reliability`).
* **`shared/kmeans_service.py` :** Singleton chargeant les artefacts `tfidf_vectorizer.pkl` et `kmeans_model.pkl`. Classifieur **de repli** utilisé par `/ask` si `ReliabilityService` n'est pas disponible.
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
       └──► Route: /grafana/  ──► proxy_pass http://grafana:3000

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
      ├── Pull des dernières modifications Git
      ├── Reconstruction des images applicatives (docker compose build)
      └── Relance à chaud des conteneurs (docker compose up -d --pull never)

```

> **Note :** Le déploiement n'est plus conditionné à la branche `main` mais à la présence d'un **tag Git** ou à un déclenchement manuel. Cela permet de déployer depuis n'importe quelle branche validée sans modifier la branche principale.

---

## 15. Configuration & Variables d'Environnement

L'ensemble des secrets et des paramètres d'infrastructure est centralisé au sein d'un fichier isolé `.env`, exclu du versionnage de code et injecté dynamiquement dans les conteneurs Docker au runtime.

| Clef de configuration | Périmètre d'impact | Rôle / Description technique |
| --- | --- | --- |
| `MONGO_CONNECTION_STRING` | Global | Chaîne d'authentification NoSQL (`mongodb://user:pass@host:port/`) |
| `BSKY_USERNAME` | Ingestion | Identifiant de compte (handle) pour l'accès à l'API Bluesky |
| `BSKY_APP_PASSWORD` | Ingestion | Jeton d'application spécifique (*App Password*) généré sur Bluesky |
| `OLLAMA_HOST` | API Applicative | Point d'accès réseau vers l'API d'Ollama (`http://ollama:11434`) |
| `OLLAMA_MODEL` | API Applicative | Désignation du modèle de langage cible (`qwen2:1.5b`) |
| `API_URL` | Interface Web | Point d'accès réseau vers le service FastAPI (`http://api:8080/`) |
| `GOOGLE_API_KEY` | Module Failover | Clé d'authentification pour le service distant de secours Gemini |

---

## 16. Cycle de Vie de la Donnée & Flux de Bout en Bout

Le diagramme de séquence ci-dessous détaille le cheminement complet de l'information au sein du système, depuis la scrutation des serveurs de Bluesky par l'orchestrateur jusqu'à l'accès en temps réel par l'utilisateur final.

```mermaid
sequenceDiagram
    participant AF as Airflow Scheduler
    participant KD as Kedro + EnergyHook
    participant BS as API Distante Bluesky
    participant MG as Base MongoDB
    participant API as FastAPI (:8080)
    participant OL as Serveur Ollama
    participant ST as Serveur Streamlit
    actor User as Utilisateur Final

    rect rgb(25, 35, 65)
        Note over AF,MG: Étape 1 : Routine d'Ingestion Périodique
        AF->>KD: Exécution : kedro run --pipeline=ingest_from_bluesky
        KD->>BS: Requête : search_posts(keyword, limit=25) sur 20 axes
        BS-->>KD: Restitution des payloads JSON (Flux brut)
        KD->>MG: Écriture de masse (insert_many) ──► Collection: posts
        KD->>MG: Enregistrement télémétrie ──► Collection: energy_logs
    end

    rect rgb(25, 55, 60)
        Note over AF,MG: Étape 2 : Transformation et Nettoyage NLP
        AF->>KD: Exécution : kedro run --pipeline=nlp_transform
        KD->>MG: Requête différentielle (Omission des unique_id existants)
        MG-->>KD: Extraction des textes bruts
        KD->>KD: Processus : clean_text() + normalize_text() (Regex, Ponctuation, ASCII)
        KD->>MG: Persistance par Upsert ──► Collection: cleaned_posts
        KD->>MG: Enregistrement télémétrie ──► Collection: energy_logs
    end

    rect rgb(25, 65, 40)
        Note over AF,MG: Étape 3 : Vectorisation et Apprentissage KMeans
        AF->>KD: Exécution : kedro run --pipeline=vectorisation
        KD->>MG: Extraction des textes nettoyés non traités
        MG-->>KD: Restitution du corpus textuel normalisé
        KD->>KD: Transformation matricielle TF-IDF (Extraction de 5000 features)
        KD->>KD: Inférence non supervisée KMeans (k=2) ──► Calcul du ratio de distances
        KD->>MG: Écriture transactionnelle groupée (bulk_write) ──► Collection: classified_posts
        KD->>KD: Export physique des artefacts sérialisés : tfidf_vectorizer.pkl / kmeans_model.pkl
        KD->>MG: Enregistrement télémétrie ──► Collection: energy_logs
    end

    rect rgb(65, 25, 30)
        Note over User,ST: Étape 4 : Requêtage Synchrone & Inférence Temps Réel
        User->>ST: Soumission d'une affirmation textuelle (Onglet Fact-Check)
        ST->>API: Requête HTTP : POST /ask {"question": "..."}
        API->>API: Interception KMeansService : Transformation à chaud & Prédiction du verdict
        API->>OL: Requête HTTP Asynchrone : POST /api/chat (Modèle qwen2:1.5b)
        OL-->>API: Restitution du rapport d'explication syntaxique
        API-->>ST: Payload JSON enrichi {verdict, probability, cluster, explanation}
        ST-->>User: Rendu graphique dynamique (Badge coloré, Jauge de confiance & Texte du LLM)
    end

```

---

## 17. Guide de Démarrage Rapide

### Prérequis Système

* Moteur Docker et extension Docker Compose v2.
* Fichier d'environnement `.env` dûment configuré à la racine du projet.
* Disponibilité d'une connexion Internet lors de la phase initiale de construction (Téléchargement des images de base et du modèle Ollama d'environ 900 Mo).

### Déploiement en Environnement de Production (AWS EC2)

L'intégration sur l'instance cloud s'effectue automatiquement via la CI/CD lors de la validation d'un commit sur la branche principale. Pour forcer manuellement une réinitialisation à chaud directement sur le serveur :

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
# Raccourci équivalent à : docker compose build --no-cache && docker compose up -d

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

# Étape 4 : Vectorisation, clustering non supervisé et génération des fichiers .pkl
make run3          # kedro run --pipeline=vectorisation

# Étape 5 : Démarrage des modules applicatifs de service
make api           # uvicorn src.api.api:app --host 0.0.0.0 --port 8080
make web           # streamlit run src/streamlit_app/streamlit_app.py

```

### Extinction de l'Infrastructure

Pour interrompre la totalité des services conteneurisés et purger les volumes éphémères associés :

```bash
make down          # docker compose down -v

```

```

```
