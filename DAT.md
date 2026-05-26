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
│  Kedro vectorisation
▼
MongoDB [Collection: classified_posts]
Artefacts (KMeans + TF-IDF) ──► FastAPI (/ask) ◄── Streamlit UI
│
Ollama LLM
(Interprétabilité NLP)
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
│   ├── kmeans_service.py                 # Moteur d'inférence synchrone
│   ├── ollama_service.py                 # Client d'inférence LLM local
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
│       ├── streamlit_app.py              # Point d'entrée IHM
│       ├── streamlit_logic.py            # Logique de présentation & requêtage
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
| **Service Web** | FastAPI | *latest* | Serveur d'API asynchrone avec validation Pydantic |
| **Serveur d'Inférence** | Uvicorn | *latest* | Serveur ASGI de production pour l'API |
| **LLM Local** | Ollama | *latest* | Moteur d'exécution pour le modèle `qwen2:1.5b` |
| **LLM Cloud (Failover)** | Google Gemini | *latest* | Solution LLM externe de secours via `google-genai` |
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
* `./data` (Volume lié à l'hôte) : Monté au sein du conteneur `api` pour assurer l'accès aux modèles sérialisés par Kedro (`.pkl`).

### Gestion de la Santé des Services (Healthchecks)

Le service `ollama` implémente une routine de démarrage robuste. Il instancie le démon `ollama serve` puis orchestre le téléchargement du modèle via `ollama pull qwen2:1.5b` (Volume d'environ 900 Mo). La sonde de santé vérifie périodiquement la disponibilité du modèle via la commande `ollama list | grep qwen2`, s'accordant un délai maximal de 300 secondes (20 tentatives d'intervalle).

---

## 5. Pipelines de Données (Framework Kedro)

Le framework **Kedro 1.0.0** est utilisé comme colonne vertébrale pour structurer le code de traitement de données. Les modules sont partitionnés en quatre pipelines distincts au sein de `pipeline_registry.py`.

Par défaut, le pipeline `__default__` exécute de manière séquentielle le cycle ETL complet :


$$\text{ingest\_from\_bluesky} \longrightarrow \text{nlp\_transform} \longrightarrow \text{vectorisation}$$

Le pipeline `model_training` est isolé volontairement de la routine par défaut. Il s'agit d'une brique d'entraînement supervisé lourd s'appuyant sur des données externes historiques.

```mermaid
flowchart LR
    BS(["🌐 API Bluesky"])
    M1[("MongoDB\nposts")]
    M2[("MongoDB\ncleaned_posts")]
    M3[("MongoDB\nclassified_posts")]
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

    BS --> N1
    N2 --> M1
    M1 --> N3
    N6 --> M2
    M2 --> N7
    N10 --> PKL
    N11 --> M3

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
  ├── classified_posts (Résultats d'inférence KMeans)
  │     └── [ _id, unique_id, username, category, normalized_text, fake_news_prob, is_real, cluster, classified_at ]
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

### Spécification des Points d'Accès (Endpoints)

#### `POST /ask`

Prend en charge l'évaluation instantanée d'une affirmation soumise par un utilisateur.

* **Contrat d'entrée (JSON) :**
```json
{ "question": "L'affirmation textuelle à analyser" }

```


* **Logique métier interne :**
1. **Phase de classification synchrone (`KMeansService`) :** Le texte subit une chaîne de nettoyage strictement identique à celle du pipeline `nlp_transform`. La chaîne nettoyée est projetée dans l'espace vectoriel TF-IDF.
* *Cas de hors-vocabulaire :* Si le vecteur ne contient aucun terme connu du dictionnaire ($nnz = 0$), l'API court-circuite le modèle et renvoie un statut indéterminé (`verdict=uncertain`, `probability=0.5`).
* *Cas nominal :* Prédiction du cluster et évaluation du score de confiance mathématique. Le score continu est traduit en verdict discret selon la matrice suivante :
* $\text{Score} \ge 0.8 \longrightarrow \text{"true"}$
* $\text{Score} \ge 0.6 \longrightarrow \text{"very likely true"}$
* $\text{Score} \ge 0.4 \longrightarrow \text{"uncertain"}$
* $\text{Score} \ge 0.2 \longrightarrow \text{"very likely false"}$
* $\text{Score} < 0.2 \longrightarrow \text{"false"}$




2. **Phase d'explication asynchrone (`OllamaService`) :** Sollicitation du LLM local `qwen2:1.5b` par une requête HTTP asynchrone (`httpx.AsyncClient`) avec une tolérance de complétion (timeout) fixée à 300 secondes. Le prompt système force le modèle à adopter une posture d'interprétabilité purement linguistique et structurelle, limitée à 2 ou 3 phrases, en lui interdisant formellement de statuer lui-même sur la véracité historique des faits. En cas de défaillance du serveur Ollama, le service dégrade son fonctionnement de manière transparente en retournant une chaîne explicative vide, préservant la réponse de classification.
3. **Télémétrie :** Incrémentation des compteurs Prometheus selon le verdict rendu.


* **Contrat de sortie (JSON) :**
```json
{
  "verdict": "true | very likely true | uncertain | very likely false | false",
  "probability": 0.9124,
  "based_on": "kmeans",
  "cluster": 1,
  "explanation": "L'analyse linguistique met en évidence une structure syntaxique informative dénuée d'artifices hyperboliques..."
}

```



#### `GET /health`

Renvoie un indicateur d'état nominal `"OK"`. Cet endpoint sert de sonde de vitalité (*liveness probe*) pour l'orchestrateur Docker.

#### `GET /metrics`

Point de collecte Prometheus automatisé par la bibliothèque `prometheus-fastapi-instrumentator`.

---

## 9. Services Partagés (`shared/`)

Les modules logés dans le répertoire `shared/` constituent la bibliothèque de composants communs réutilisés de manière transverse par les pipelines Kedro, l'API FastAPI et le tableau de bord Streamlit.

* **`shared/mongo.py` :** Encapsulation du client de connexion PyMongo. Fournit la méthode d'accès sécurisé aux collections de la base `bluesky_db`.
* **`shared/energy_service.py` :** Couche d'abstraction pour l'archivage et la récupération des journaux d'émissions carbone stockés dans la collection `energy_logs`.
* **`shared/kmeans_service.py` :** Patron de conception **Singleton** garantissant l'unicité du chargement en mémoire des fichiers sérialisés `tfidf_vectorizer.pkl` et `kmeans_model.pkl`. Lève une exception explicite au démarrage si les artefacts s'avèrent introuvables.
* **`shared/ollama_service.py` :** Connecteur asynchrone gérant la communication avec l'API HTTP du conteneur Ollama local.
* **`shared/gemini_service.py` :** Module redondant de secours s'appuyant sur le SDK officiel `google-genai` pour déporter l'analyse textuelle sur le cloud public en cas de surcharge des ressources locales.
* **`shared/rag.py` :** Moteur autonome de recherche par similarité cosinus s'appuyant sur un index pré-calculé (`rag_vectors.joblib`). Permet l'injection de contexte connexe au sein d'un prompt LLM (non actif sur l'API de production principale).
* **`shared/llm_interface.py` :** Classe abstraite pure définissant le contrat d'interface commun (`send_message`) pour l'ensemble des intégrations de modèles de langage.
* **`shared/metrics.py` :** Déclaration centralisée des métriques Prometheus applicatives (`fakenews_verdict_total`, `fakenews_llm_latency_seconds`).

---

## 10. Interface Utilisateur (Streamlit)

L'IHM de restitution et d'interaction est déployée via Streamlit sur le port interne `8501`, puis exposée de manière publique sur le port standard HTTP `80` par le proxy inverse.

### Architecture fonctionnelle des sections

#### Onglet 1 : Fact-Check (Espace de dialogue interactif)

* Formulaire de saisie utilisateur de type chat (`st.chat_input`).
* Transmission asynchrone vers le endpoint `/ask` de l'API.
* Restitution des résultats enrichie visuellement par des composants graphiques avancés : application d'un code couleur dynamique indexé sur la sévérité du verdict, affichage d'une jauge de confiance personnalisée dotée d'un effet visuel lumineux (*glow* CSS) et affichage séquentiel de l'argumentaire généré par le LLM.
* Persistance locale de l'historique de discussion au sein de la structure éphémère `st.session_state`.

#### Onglet 2 : Analytics (Statistiques du corpus)

* Synthèse macroscopique du volume global de données via des cartes d'indicateurs (KPI Cards) : volume de posts, décompte d'auteurs uniques, diversité des thématiques.
* Restitution graphique animée via la bibliothèque Altair répartie sur quatre sous-sections :
* *Keywords :* Histogramme des 20 lemmes les plus fréquents (avec l'application d'une liste d'exclusion des mots vides (*stopwords*) français et anglais directement côté client).
* *Authors :* Diagrammes circulaires segmentés par catégorie décrivant la distribution des contributeurs les plus actifs (Palette de couleurs *Viridis*).
* *By Hour :* Graphique d'aire (*area chart*) de la distribution temporelle horaire des publications.
* *Emotions :* Analyse comparative de la répartition Fake vs Real.


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
[Événement Push / PR]
       │
       ├──► Exécution en parallèle : Job [analysis] (Scan Trivy de vulnérabilités FS & Config)
       │
       ▼
Job [lint]
 ├── Validation syntaxique de style : ruff check
 ├── Analyse de la qualité de programmation : pylint
 ├── Validation des structures de configuration : yamllint
 └── Audit de conformité des couches de conteneurisation : hadolint (4 Dockerfiles)
       │
       ▼
Job [test] (Dépendant du succès de lint)
 ├── Extraction sécurisée des secrets GitHub (Variables d'environnement de test)
 └── Exécution des tests unitaires et d'intégration : pytest --cov
       │
       ▼
Job [deploy] (Dépendant du succès de test - Limité à la branche main)
 └── Connexion SSH sécurisée sur l'instance AWS EC2 cible
      ├── Pull des dernières modifications Git
      ├── Reconstruction des images applicatives (docker compose build)
      └── Relance à chaud des conteneurs (docker compose up -d --pull never)

```

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
