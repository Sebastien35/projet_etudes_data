# Document d'Architecture Technique — FakeShield

> Projet M1 Data Science — Détection de fake news sur Bluesky

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structure du dépôt](#2-structure-du-dépôt)
3. [Pile technologique](#3-pile-technologique)
4. [Infrastructure Docker](#4-infrastructure-docker)
5. [Pipeline de données — Kedro](#5-pipeline-de-données--kedro)
   - 5.1 [ingest_from_bluesky](#51-ingest_from_bluesky)
   - 5.2 [nlp_transform](#52-nlp_transform)
   - 5.3 [vectorisation](#53-vectorisation)
   - 5.4 [model_training (hors pipeline par défaut)](#54-model_training-hors-pipeline-par-défaut)
6. [Couche de persistance — MongoDB](#6-couche-de-persistance--mongodb)
7. [Monitoring énergétique — EnergyHook](#7-monitoring-énergétique--energyhook)
8. [API de classification — FastAPI](#8-api-de-classification--fastapi)
9. [Services partagés (`shared/`)](#9-services-partagés-shared)
10. [Interface web — Streamlit](#10-interface-web--streamlit)
11. [Reverse proxy — Nginx](#11-reverse-proxy--nginx)
12. [Observabilité — Prometheus](#12-observabilité--prometheus)
13. [Orchestration — Apache Airflow](#13-orchestration--apache-airflow)
14. [CI/CD — GitHub Actions](#14-cicd--github-actions)
15. [Variables d'environnement](#15-variables-denvironnement)
16. [Flux de données de bout en bout](#16-flux-de-données-de-bout-en-bout)
17. [Démarrage rapide](#17-démarrage-rapide)

---

## 1. Vue d'ensemble

FakeShield est une plateforme de détection automatique de fake news appliquée aux posts du réseau social décentralisé **Bluesky**. Elle est composée de quatre pipelines Kedro, d'une API de classification temps réel, et d'un tableau de bord Streamlit.

Le système suit une architecture **ETL → ML → API → UI** :

```
Bluesky API
    │  atproto (keyword search)
    ▼
MongoDB · posts
    │  Kedro nlp_transform
    ▼
MongoDB · cleaned_posts
    │  Kedro vectorisation
    ▼
MongoDB · classified_posts
KMeans + TF-IDF artifacts ──► FastAPI /ask ──► Streamlit UI
                                   │
                               Ollama LLM
                           (explication NLP)
```

---

## 2. Structure du dépôt

```
projet_etudes_data/
├── conf/
│   ├── base/
│   │   ├── catalog.yml                  # Datasets Kedro (CSV Kaggle)
│   │   ├── parameters.yml
│   │   ├── parameters_ingest_from_bluesky.yml
│   │   ├── parameters_nlp_transform.yml
│   │   ├── parameters_vectorisation.yml  # n_clusters, max_features, chemins artefacts
│   │   └── parameters_model_training.yml # vocab_size, max_len, epochs, batch_size
│   ├── airflow/                          # Variante de config pour Airflow
│   ├── nginx.conf                        # Reverse proxy
│   ├── prometheus.yml                    # Scrape config (désactivé en prod)
│   └── logging.yml
├── data/
│   ├── 01_raw/                           # True.csv, Fake.csv (Kaggle, non versionnés)
│   └── 06_models/                        # tfidf_vectorizer.pkl, kmeans_model.pkl
│                                         # lstm_model.keras, lstm_tokenizer.pkl
├── dags/                                 # DAGs générés par kedro-airflow
├── shared/                               # Modules partagés API ↔ Streamlit ↔ Kedro
│   ├── mongo.py
│   ├── energy_service.py
│   ├── kmeans_service.py
│   ├── ollama_service.py
│   ├── gemini_service.py                 # Backup LLM (non utilisé par l'API courante)
│   ├── lstm_service.py
│   ├── rag.py
│   ├── llm_interface.py
│   └── metrics.py
├── src/
│   ├── api/api.py                        # FastAPI
│   ├── projet_etudes/
│   │   ├── hooks.py                      # EnergyHook, SparkHooks
│   │   ├── pipeline_registry.py
│   │   ├── settings.py
│   │   └── pipelines/
│   │       ├── ingest_from_bluesky/
│   │       ├── nlp_transform/
│   │       ├── vectorisation/
│   │       └── model_training/
│   └── streamlit_app/
│       ├── streamlit_app.py
│       ├── streamlit_logic.py
│       ├── streamlit_color_chart.py
│       ├── streamlit_config.py
│       └── config.toml
├── Dockerfile.api
├── Dockerfile.airflow
├── Dockerfile.streamlit
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

---

## 3. Pile technologique

| Couche | Technologie | Version |
|---|---|---|
| Langage | Python | ≥ 3.10, < 3.15 |
| Gestionnaire de paquets | uv | latest |
| Orchestration de pipelines | Kedro | ~1.0.0 |
| Ingestion réseau social | atproto | 0.0.63 |
| Stockage | MongoDB | latest (PyMongo) |
| ML — Vectorisation | scikit-learn TF-IDF + KMeans | ~1.5.1 |
| ML — Entraînement supervisé | TensorFlow / Keras LSTM | latest |
| API | FastAPI + Uvicorn | latest |
| LLM local | Ollama — modèle qwen2:1.5b | latest |
| LLM cloud (backup) | Google Gemini (google-genai) | latest |
| Interface web | Streamlit | latest |
| Visualisation | Altair | latest |
| Monitoring énergétique | CodeCarbon | latest |
| Métriques | Prometheus (prometheus-client) | latest |
| Orchestration DAGs | Apache Airflow | 2.8.4 |
| Reverse proxy | Nginx | alpine |
| Base de données Airflow | MariaDB | latest |
| Containerisation | Docker Compose | v2 |
| CI | GitHub Actions | — |
| Linting | Black, Ruff | black latest, ruff ~0.12.0 |
| Linting Dockerfile | hadolint | v3.1.0 |
| Tests | pytest + pytest-cov | ~7.2 |

---

## 4. Infrastructure Docker

**Environnement de production :** EC2 Amazon Linux 2023 (`t`-type), Docker Compose v2. Le dépôt est cloné dans `~/<repo_name>` sur l'instance. Le déploiement est déclenché automatiquement par le pipeline CI/CD (push sur `main`).

Le fichier `docker-compose.yml` définit dix services. Les ports exposés sur l'hôte sont :

| Service | Image / Build | Port hôte | Port conteneur | Rôle |
|---|---|---|---|---|
| `nginx` | nginx:alpine | 80 | 80 | Reverse proxy public |
| `airflow-webserver` | Dockerfile.airflow | — | 8080 | UI Airflow (via /airflow/) |
| `airflow-scheduler` | Dockerfile.airflow | — | — | Planificateur DAGs |
| `airflow-init` | Dockerfile.airflow | — | — | Init DB + user admin (one-shot) |
| `database` | mariadb:latest | 3360 | 3306 | Métadonnées Airflow |
| `ollama` | ollama/ollama | — | 11434 | LLM local (interne uniquement) |
| `api` | Dockerfile.api | 8080 | 8080 | FastAPI classification |
| `streamlit` | Dockerfile.streamlit | — | 8501 | Interface web (via nginx /) |
| `prometheus` | prom/prometheus | 9090 | 9090 | Collecte de métriques |
| `grafana` | grafana/grafana | 3000 | 3000 | Dashboards (via nginx /grafana/) |
| `node-exporter` | prom/node-exporter | — | — | Métriques système hôte |

**Dépendances de démarrage (Docker Compose `depends_on`) :**

```
nginx ─────────────┬──► streamlit
                   └──► airflow-webserver
streamlit ─────────────► api (healthcheck)
api ────────────────────► ollama (healthcheck)
airflow-webserver ──────► airflow-init (service_completed_successfully)
airflow-scheduler ──────► airflow-init (service_completed_successfully)
airflow-init ───────────► database
```

**Volumes persistants :**
- `airflow-logs` — logs des DAGs
- `airflow-plugins` — plugins Airflow
- `ollama-data` — modèles LLM téléchargés (`qwen2:1.5b`)
- `./data` monté dans `api` — artefacts KMeans/TF-IDF générés par Kedro

**Ollama — démarrage :** le conteneur lance `ollama serve` puis exécute `ollama pull qwen2:1.5b` (~900 MB). Le healthcheck attend que `ollama list | grep qwen2` réponde (jusqu'à 300 s, 20 tentatives).

**Images Docker :**

- `Dockerfile.api` : python:3.12-slim, uv pip install (fastapi, uvicorn, scikit-learn, httpx, pymongo…), copie `shared/` et `src/api/`, expose 8080.
- `Dockerfile.streamlit` : python:3.12-slim, uv pip install (streamlit, altair, pandas, pymongo…), copie `shared/` et `src/streamlit_app/`, `config.toml` → `/app/.streamlit/`, expose 8501.
- `Dockerfile.airflow` : apache/airflow:2.8.4-python3.10, uv pip install (kedro, kedro-airflow, atproto, codecarbon, scikit-learn…), correctif `typing_extensions` pour compatibilité pydantic-core.

---

## 5. Pipeline de données — Kedro

Le framework **Kedro 1.0.0** structure l'ensemble des transformations de données. Quatre pipelines sont enregistrés dans `pipeline_registry.py`.

Le pipeline `__default__` enchaîne automatiquement :

```
ingest_from_bluesky + nlp_transform + vectorisation
```

`model_training` est exclu du `__default__` — c'est une étape ponctuelle d'entraînement supervisé sur données Kaggle.

### 5.1 `ingest_from_bluesky`

**Objectif :** Récupérer des posts Bluesky par recherche par mots-clés et les stocker dans MongoDB.

**Nodes :**

| Node | Fonction | Input | Output |
|---|---|---|---|
| `fetch_from_keywords_node` | `fetch_from_keywords` | — | `posts` (list) |
| `save_posts_to_db_node` | `save_posts_to_db` | `posts` | — |

**Détail de `fetch_from_keywords` :**

- Authentification via `atproto.Client.login()` avec `BSKY_USERNAME` / `BSKY_APP_PASSWORD`.
- Recherche sur 4 thèmes prédéfinis et leurs mots-clés associés :

| Thème | Mots-clés |
|---|---|
| Discover | news, world news, science, technology, research |
| Trending | breaking news, urgent, live updates, alert |
| Hot Topics | politics, election, climate, crisis, economy, AI |
| Misinformation | fact check, debunked, misinformation, conspiracy, hoax |

- Appel `app.bsky.feed.search_posts(q=keyword, limit=25, lang="en")` pour chaque mot-clé.
- Déduplication : les `unique_id` déjà présents dans `posts` sont exclus. Un `unique_id` est construit comme `{username}_{created_at}`.
- Un `seen_uris` évite les doublons intra-requête (même post remonté par plusieurs mots-clés).
- Les posts sans `text` ou `created_at` sont ignorés.

**Détail de `save_posts_to_db` :**

- Insert en masse (`insert_many`) dans la collection `posts`.
- Champs persistés : `text`, `username`, `created_at`, `unique_id`, `utc_saved_at` (UTC), `category`.

**Commande :** `kedro run --pipeline=ingest_from_bluesky` ou `make run1`

---

### 5.2 `nlp_transform`

**Objectif :** Nettoyer et normaliser les posts bruts pour préparer la vectorisation.

**Nodes :**

| Node | Fonction | Input | Output |
|---|---|---|---|
| `get_posts_to_treat_node` | `get_posts_to_treat` | — | `raw_posts` (DataFrame) |
| `clean_text_node` | `clean_text` | `raw_posts` | `cleaned_posts` |
| `normalize_text_node` | `normalize_text` | `cleaned_posts` | `normalized_posts` |
| `save_to_db_node` | `save_to_db` | `normalized_posts` | — |

**`get_posts_to_treat` :** récupère uniquement les posts de `posts` dont le `unique_id` n'est pas encore dans `cleaned_posts` (traitement incrémental).

**`clean_text` — transformations appliquées :**

1. Passage en minuscules
2. Suppression des URLs (`http\S+|www\S+`)
3. Suppression des mentions (`@\w+`)
4. Suppression des hashtags (`#\w+`)
5. Suppression des emojis (plages Unicode U+1F600–U+1F6FF, U+1F1E0–U+1F1FF)
6. Suppression de la ponctuation (`str.maketrans`)

Résultat stocké dans la colonne `clean_text`.

**`normalize_text` — transformations appliquées :**

1. Normalisation Unicode NFKD
2. Encodage ASCII (ignorer les caractères non-ASCII)
3. Collapsage des espaces multiples en un seul

Résultat stocké dans la colonne `normalized_text`.

**`save_to_db` :** upsert document par document dans `cleaned_posts`. Champs persistés : `username`, `created_at`, `unique_id`, `utc_saved_at`, `category`, `normalized_text`.

**Commande :** `kedro run --pipeline=nlp_transform` ou `make run2`

---

### 5.3 `vectorisation`

**Objectif :** Vectoriser les posts nettoyés, appliquer un clustering KMeans, persister les prédictions et sauvegarder les artefacts modèle pour l'API.

**Paramètres (`conf/base/parameters_vectorisation.yml`) :**

```yaml
vectorisation:
  n_clusters: 2
  max_features: 5000
  vectorizer_path: "data/06_models/tfidf_vectorizer.pkl"
  kmeans_path:     "data/06_models/kmeans_model.pkl"
```

**Nodes :**

| Node | Fonction | Input | Output |
|---|---|---|---|
| `get_cleaned_posts_node` | `get_cleaned_posts` | — | `texts` (list[str]), `posts_` (list[dict]) |
| `vectorize_texts_node` | `vectorize_texts` | `texts`, `max_features` | `tfidf_matrix`, `tfidf_vectorizer` |
| `cluster_posts_node` | `cluster_posts` | `tfidf_matrix`, `n_clusters` | `labels`, `probs`, `km_model` |
| `save_model_artifacts_node` | `save_model_artifacts` | `tfidf_vectorizer`, `km_model`, chemins | — |
| `save_predictions_node` | `save_predictions` | `posts_`, `probs`, `labels` | — |

**`get_cleaned_posts` :** récupère les posts de `cleaned_posts` dont le `unique_id` n'est pas encore dans `classified_posts` (traitement incrémental).

**`vectorize_texts` :** `TfidfVectorizer(max_features=5000, sublinear_tf=True)`. La matrice TF-IDF résultante a pour dimensions `(n_posts, 5000)`.

**`cluster_posts` :** `KMeans(n_clusters=2, random_state=42, n_init="auto")`.

Convention de labellisation :
- **Cluster 1** → `is_real = True`
- **Cluster 0** → `is_real = False` (fake)

Score de "réalité" calculé par ratio de distances aux centroïdes :

```
d0 = distance au centroïde 0 (fake)
d1 = distance au centroïde 1 (real)
score = d0 / (d0 + d1 + 1e-8)
```

Un score élevé (distance grande au centroïde fake) → post considéré réel.

**`save_model_artifacts` :** sérialise le `TfidfVectorizer` et le `KMeans` en fichiers pickle dans `data/06_models/`. Ces fichiers sont montés dans le conteneur `api` via le volume `./data:/app/data`.

**`save_predictions` :** upsert bulk (`bulk_write` avec `UpdateOne(..., upsert=True)`) dans `classified_posts`. Champs persistés : `unique_id`, `username`, `category`, `normalized_text`, `fake_news_prob` (float), `is_real` (bool), `cluster` (int), `classified_at`.

**Commande :** `kedro run --pipeline=vectorisation` ou `make run3`

---

### 5.4 `model_training` (hors pipeline par défaut)

**Objectif :** Entraîner un classifieur LSTM supervisé sur le dataset Kaggle « Fake and Real News ».

**Source de données :** `data/01_raw/True.csv` et `data/01_raw/Fake.csv` (déclarés dans `conf/base/catalog.yml`). À télécharger manuellement depuis [Kaggle](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset).

**Paramètres (`conf/base/parameters_model_training.yml`) :**

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

**Nodes :**

| Node | Fonction | Description |
|---|---|---|
| `load_training_data` | Combine True.csv + Fake.csv | label=1 pour vrais, label=0 pour fake. Concatène `title + text` si les deux colonnes existent. Shuffle aléatoire. |
| `preprocess_training_data` | Nettoyage + split | Lowercase, suppression URLs, caractères non-alphabétiques. Split stratifié 80/20. |
| `build_tokenizer_and_sequences` | Tokenisation Keras | `Tokenizer(num_words=5000, oov_token="<OOV>")`. Padding post-séquence à `max_len=200`. |
| `build_lstm_model` | Architecture Keras | Voir ci-dessous. |
| `train_lstm` | Entraînement | EarlyStopping sur `val_accuracy`, patience=3, restore_best_weights. |
| `save_lstm_artifacts` | Persistance | Modèle en `.keras`, tokenizer en pickle. |

**Architecture LSTM :**

```
Embedding(5000, 128, input_length=200)
LSTM(128, return_sequences=True)
Dropout(0.5)
LSTM(64)
Dropout(0.5)
Dense(32, activation='relu')
Dense(1, activation='sigmoid')
```
Compilation : `optimizer=adam`, `loss=binary_crossentropy`, `metrics=[accuracy]`.

**Commande :** `kedro run --pipeline=model_training`

> Note : ce pipeline n'est pas utilisé par l'API courante. L'API s'appuie exclusivement sur KMeans (`vectorisation`).

---

## 6. Couche de persistance — MongoDB

**Base de données :** `bluesky_db`

**Connection string :** variable d'environnement `MONGO_CONNECTION_STRING`. Le client est instancié dans `shared/mongo.py` via `pymongo.MongoClient`.

**Collections :**

| Collection | Rôle | Champs principaux |
|---|---|---|
| `posts` | Posts bruts ingérés depuis Bluesky | `unique_id`, `username`, `text`, `created_at`, `category`, `utc_saved_at` |
| `cleaned_posts` | Posts après nettoyage NLP | `unique_id`, `username`, `created_at`, `category`, `normalized_text`, `utc_saved_at` |
| `classified_posts` | Résultats du clustering KMeans | `unique_id`, `username`, `category`, `normalized_text`, `fake_news_prob`, `is_real`, `cluster`, `classified_at` |
| `energy_logs` | Mesures de consommation par nœud Kedro | `pipeline_name`, `node_name`, `run_id`, `timestamp`, `duration_s`, `energy_kwh`, `cpu_power_w`, `gpu_power_w`, `ram_power_w`, `co2_kg`, `cpu_energy_kwh`, `gpu_energy_kwh`, `ram_energy_kwh` |

**Traitement incrémental :** les pipelines `nlp_transform` et `vectorisation` n'opèrent que sur les documents non encore traités, en comparant les `unique_id` entre collections via `distinct("unique_id")`.

---

## 7. Monitoring énergétique — EnergyHook

**Fichier :** `src/projet_etudes/hooks.py`

`EnergyHook` est un hook Kedro qui mesure la consommation énergétique de chaque nœud de pipeline en temps réel.

**Mécanisme :**

- `before_pipeline_run` : capture le nom du pipeline en cours (`run_params["pipeline_name"]`).
- `before_node_run` : instancie un `codecarbon.EmissionsTracker(save_to_file=False, measure_power_secs=1)` et appelle `tracker.start()`. Le tracker est stocké dans `self._trackers[node.name]`.
- `after_node_run` : appelle `tracker.stop()`, récupère les données via `tracker.final_emissions_data` et appelle `shared.energy_service.save_energy_log(...)`.

**Données mesurées par nœud :**

| Métrique | Unité | Champ MongoDB |
|---|---|---|
| Durée | secondes | `duration_s` |
| Énergie totale | kWh | `energy_kwh` |
| Puissance CPU | W | `cpu_power_w` |
| Puissance GPU | W | `gpu_power_w` |
| Puissance RAM | W | `ram_power_w` |
| Émissions CO₂ | kg | `co2_kg` |
| Énergie CPU | kWh | `cpu_energy_kwh` |
| Énergie GPU | kWh | `gpu_energy_kwh` |
| Énergie RAM | kWh | `ram_energy_kwh` |

Le hook est résilient : toute erreur CodeCarbon est capturée et loguée en `WARNING` sans interrompre l'exécution du pipeline.

**Hook secondaire `SparkHooks` :** tente d'initialiser une `SparkSession` si une configuration `spark.yaml` est présente dans `conf/`. Échoue silencieusement sinon (usage optionnel).

---

## 8. API de classification — FastAPI

**Fichier :** `src/api/api.py`
**Port :** 8080
**Commande locale :** `make api` → `uvicorn src.api.api:app --host 0.0.0.0 --port 8080`

### Endpoints

#### `POST /ask`

**Corps de la requête :**
```json
{ "question": "string" }
```

**Logique d'exécution :**

1. **Classification KMeans** (synchrone) — `KMeansService.classify(question)` :
   - Prétraitement identique au pipeline (`nlp_transform`) : lowercase, suppression URLs/mentions/hashtags/emojis/ponctuation, NFKD + ASCII.
   - Transformation TF-IDF (`vectorizer.transform`).
   - Si `vec.nnz == 0` (aucun vocabulaire commun avec le corpus) : retourne `verdict=uncertain, probability=0.5`.
   - Sinon : `km.predict(vec)` + calcul du score par ratio de distances.
   - Mapping score → verdict :

   | Score | Verdict |
   |---|---|
   | ≥ 0.8 | `true` |
   | ≥ 0.6 | `very likely true` |
   | ≥ 0.4 | `uncertain` |
   | ≥ 0.2 | `very likely false` |
   | < 0.2 | `false` |

2. **Explication Ollama** (asynchrone, best-effort) — `OllamaService.explain(...)` :
   - Appel HTTP POST async à `http://ollama:11434/api/chat` via `httpx.AsyncClient(timeout=300.0)`.
   - Modèle : `qwen2:1.5b` (configurable via `OLLAMA_MODEL`).
   - Prompt système : rôle d'assistant d'interprétabilité ML, analyse linguistique et structurelle uniquement, 2-3 phrases de réponse imposées, refus de commenter la vérité factuelle.
   - En cas d'échec Ollama : `result["explanation"] = ""`, sans erreur client.

3. **Métriques Prometheus** : incrémentation de `VERDICT_COUNTER.labels(verdict=...)`.

**Corps de réponse :**
```json
{
  "verdict":     "true | very likely true | uncertain | very likely false | false",
  "probability": 0.0000,
  "based_on":    "kmeans",
  "cluster":     0,
  "explanation": "..."
}
```

#### `GET /health`

Retourne `"OK"`. Utilisé par le healthcheck Docker du service `api`.

#### `GET /metrics`

Endpoint Prometheus exposé automatiquement par `prometheus-fastapi-instrumentator`. Expose notamment `fakenews_verdict_total` et `fakenews_llm_latency_seconds`.

### Singleton KMeansService

`shared/kmeans_service.py` implémente un singleton (`_instance` global) chargé à la première requête. Charge `tfidf_vectorizer.pkl` et `kmeans_model.pkl` depuis `data/06_models/`. Une `FileNotFoundError` explicite est levée si les artefacts sont absents, avec instruction de lancer la pipeline `vectorisation`.

---

## 9. Services partagés (`shared/`)

Ces modules sont importés à la fois par l'API, le Streamlit et les pipelines Kedro.

### `shared/mongo.py`

Classe `mongo_client` : wraps `pymongo.MongoClient` pointant sur `bluesky_db`. Méthode `use_collection(name)` retourne la collection correspondante.

### `shared/energy_service.py`

- `save_energy_log(...)` : insert un document dans `energy_logs`.
- `get_energy_logs()` : retourne tous les documents triés par `timestamp` décroissant.

### `shared/kmeans_service.py`

Singleton `KMeansService` (voir §8). Méthode `classify(text) -> dict`.

### `shared/ollama_service.py`

`OllamaService(LLMInterface)` : client HTTP asynchrone vers Ollama. Modèle par défaut : `qwen2:1.5b`. Timeout 300 s (la première inférence peut prendre 2-3 min en CPU).

### `shared/gemini_service.py`

`GeminiService(LLMInterface)` : client Google Gemini via `google.genai`. Méthode `explain(claim, verdict, probability) -> str`. Non utilisé par l'API courante (backup / développement).

### `shared/rag.py`

`Rag` : moteur de recherche TF-IDF pour la Retrieval Augmented Generation. Charge un index pré-calculé (`data/06_models/rag_vectors.joblib`), reconstruit la matrice TF-IDF, et expose `retrieve_context(query, top_k=5)` via similarité cosinus. Non utilisé par l'API courante.

### `shared/llm_interface.py`

Interface abstraite `LLMInterface` : définit `model_name`, `api_key`, et la méthode `send_message`. Base commune à `GeminiService` et `OllamaService`.

### `shared/metrics.py`

Métriques Prometheus :

| Nom | Type | Labels | Description |
|---|---|---|---|
| `fakenews_verdict_total` | Counter | `verdict` | Nombre de verdicts rendus par label |
| `fakenews_retrieval_total` | Counter | `source` | Source de récupération : rag / general_knowledge / error |
| `fakenews_llm_latency_seconds` | Histogram | — | Durée appel LLM (buckets : 0.5s à 60s) |
| `fakenews_rag_context_chars` | Histogram | — | Taille du contexte RAG en caractères |

---

## 10. Interface web — Streamlit

**Fichier :** `src/streamlit_app/streamlit_app.py`
**Port :** 8501 (exposé publiquement via nginx sur `:80`)
**Commande locale :** `make web` → `streamlit run src/streamlit_app/streamlit_app.py`

### Architecture visuelle

L'interface est organisée en **3 onglets** :

#### Onglet 1 — Fact-Check

Interface de chatbot permettant de soumettre n'importe quelle affirmation à l'API `/ask`.

- `st.chat_input` pour la saisie utilisateur.
- Appel `send_message_api(user_input)` → POST `{API_URL}/ask`.
- Affichage du résultat : badge verdict coloré (couleur dépend du verdict), barre de confiance (gradient CSS avec glow), explication Ollama, source du classifieur.
- Historique de conversation stocké dans `st.session_state.messages`.
- Bouton « Clear conversation » qui vide l'historique et appelle `st.rerun()`.

**Mapping verdict → couleur :**

| Verdict | Couleur |
|---|---|
| true | #34d399 (emerald) |
| very likely true | #6ee7b7 |
| uncertain | #fbbf24 (amber) |
| very likely false | #fb923c |
| false / error | #f87171 (coral) |

#### Onglet 2 — Analytics

Tableau de bord statistique sur le corpus Bluesky.

- 4 métriques cards : nombre de posts, auteurs uniques, catégories, mot-clé le plus fréquent.
- 4 graphiques Altair (chaque graphique dans un sous-onglet) :
  - **Keywords** : graphique bar + point + rule des 20 mots-clés les plus fréquents (TF-IDF blacklist de stopwords FR/EN appliquée côté Streamlit).
  - **Authors** : donut charts par catégorie, top 8 auteurs (schéma `viridis`).
  - **By Hour** : area chart de la distribution horaire des posts.
  - **Emotions** : bar chart horizontal Fake vs Real (couleurs : emerald / coral).

- Données chargées via `@st.cache_data(ttl=300)` pour éviter des requêtes MongoDB répétées.
- Bouton « Reload data » qui vide le cache et relance.

#### Onglet 3 — Energy Report

Rapport de consommation énergétique des pipelines Kedro.

- 4 métriques cards : énergie totale (Wh), CO₂ total (mg), nombre de runs, nœud le plus énergivore.
- 4 graphiques Altair (sous-onglets) :
  - **By Pipeline** : bar chart horizontal, énergie totale par pipeline.
  - **By Node** : bar chart horizontal, énergie totale par nœud, coloré par pipeline.
  - **Breakdown** : bar chart empilé CPU / RAM / GPU par nœud (énergie moyenne par run).
  - **Timeline** : scatter plot des runs dans le temps, coloré par pipeline.
- Tableau des 40 derniers runs (timestamp, pipeline, nœud, Wh, CO₂ mg, durée s).
- Données chargées via `@st.cache_data(ttl=60)`.
- Bouton « Reload energy data ».

**Couleurs pipelines :**

| Pipeline | Couleur |
|---|---|
| ingest_from_bluesky | #60a5fa (electric blue) |
| nlp_transform | #c084fc (violet) |
| vectorisation | #34d399 (emerald) |
| default | #fbbf24 (amber) |

### Design

Thème **dark glassmorphism** inspiré de visionOS :
- Fond : `#050510` (navy void), aurora animée par 4 orbes CSS `@keyframes` à positions et cycles indépendants (20-38 s).
- Glass cards : `rgba(255,255,255,0.04)`, `backdrop-filter: blur(28px)`, `inset 0 1px 0 rgba(255,255,255,0.06)`.
- Accent : violet électrique `#a78bfa` avec glow `box-shadow`.
- Thème Streamlit natif configuré dans `src/streamlit_app/config.toml` (`base=dark`, `primaryColor=#a78bfa`).
- Polices : Inter (Google Fonts).

### `streamlit_logic.py`

Module de logique métier côté Streamlit :
- `get_posts()` → collection `cleaned_posts`, retourne un DataFrame avec `username`, `created_at`, `category`, `normalized_text`.
- `get_classified_posts()` → collection `classified_posts`, retourne un DataFrame avec `label` (Real/Fake).
- `top_users_per_category(df, top_k=10)` → top k auteurs par catégorie.
- `trending_keywords(df, top_k=20)` → fréquence des tokens (hors stopwords FR/EN prédéfinis).
- `posts_per_hour(df)` → distribution horaire des posts.
- `fake_real_distribution(df)` → compte Fake / Real.
- `get_energy_df()` → conversion des logs énergie (kWh → Wh, kg → mg CO₂).
- `energy_by_pipeline(df)`, `energy_by_node(df)`, `energy_timeline(df)` → agrégations pandas.

---

## 11. Reverse proxy — Nginx

**Fichier :** `conf/nginx.conf`

```
GET /*          → proxy_pass http://streamlit:8501
                  proxy_set_header Upgrade $http_upgrade (WebSocket)
GET /airflow/*  → proxy_pass http://airflow-webserver:8080/airflow/
GET /grafana/*  → proxy_pass http://grafana:3000
```

Streamlit nécessite un upgrade WebSocket (`Connection: upgrade`) pour le rechargement dynamique. Airflow est exposé sous `/airflow/` avec `AIRFLOW__WEBSERVER__BASE_URL=http://localhost/airflow` côté conteneur. Grafana est exposé sous `/grafana/` avec `GF_SERVER_ROOT_URL` et `GF_SERVER_SERVE_FROM_SUB_PATH=true` côté conteneur.

**Note :** Nginx écoute uniquement sur le port 80 (HTTP). HTTPS n'est pas configuré — utiliser `http://` pour accéder à l'instance EC2.

---

## 12. Observabilité — Prometheus & Grafana

**Fichiers :** `conf/prometheus.yml`, `conf/grafana/`

Les services `prometheus` et `grafana` sont **déployés** dans `docker-compose.yml`.

- Prometheus scrape l'API sur `/metrics` (port 8080) et le `node-exporter` pour les métriques système (CPU, RAM, disque).
- Grafana s'appuie sur Prometheus comme datasource ; dashboards provisionnés automatiquement via `conf/grafana/provisioning/` et `conf/grafana/dashboards/`.
- Grafana est accessible en mode anonyme (`GF_AUTH_ANONYMOUS_ENABLED=true`, rôle `Viewer`).

**Accès :** `http://<EC2_IP>/grafana/`

**`node-exporter`** : conteneur `prom/node-exporter` monté sur `/proc`, `/sys`, `/` (mode `pid: host`) — expose les métriques hôte sans port public.

---

## 13. Orchestration — Apache Airflow

**Version :** 2.8.4 (python3.10)
**Executor :** `LocalExecutor`
**Base de données de métadonnées :** MariaDB (`projet_etudes_db`)
**DAGs :** générés par `kedro-airflow` dans `dags/`

Airflow est utilisé pour **planifier l'exécution périodique** des pipelines Kedro (ingestion, transformation, classification). Les DAGs sont générés à partir du registre Kedro via `kedro-airflow`.

**Accès UI :** `http://localhost/airflow/` (via nginx)
**Credentials par défaut :** `admin` / `admin` (créés par `airflow-init`)

**Initialisation :**
1. `airflow-init` attend que la DB MariaDB soit disponible (30 tentatives × 5 s).
2. `airflow db init` + création de l'utilisateur admin.
3. `airflow-webserver` et `airflow-scheduler` démarrent une fois `airflow-init` terminé.

---

## 14. CI/CD — GitHub Actions

**Fichier :** `.github/workflows/ci.yml`
**Déclencheurs :** push ou pull request sur les branches `main`, `dev`, `ci`

Les jobs s'enchaînent en séquence : **lint → test → deploy**. Le job `analysis` s'exécute en parallèle, indépendamment.

### Job `lint`

1. Checkout du code
2. Installation de `uv` + `uv python install 3.10` + `uv sync --extra dev`
3. `ruff check .` — analyse statique
4. `pylint src/` — analyse de qualité
5. `yamllint .` — validation YAML
6. `hadolint` sur les 4 Dockerfiles (`Dockerfile`, `Dockerfile.airflow`, `Dockerfile.api`, `Dockerfile.streamlit`)

### Job `test` *(needs: lint)*

1. Checkout + setup uv identique
2. Injection des secrets GitHub comme variables d'environnement via `jq` (`toJson(secrets)`) — pour les tests nécessitant les credentials Bluesky / MongoDB
3. `uv run pytest`

### Job `deploy` *(needs: test, main uniquement)*

SSH sur l'instance EC2 via `appleboy/ssh-action@v1` :

```bash
cd ~/<repo_name>
git pull origin main
docker compose build
docker compose up -d --pull never
```

`--pull never` empêche Docker de tenter de puller les images custom depuis un registry externe.

**Secrets requis :** `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`

### Job `analysis` *(parallèle, toutes branches)*

Scan de sécurité Trivy en deux passes :
1. `scan-type: fs` — vulnérabilités dans les dépendances (requirements, pyproject.toml…)
2. `scan-type: config` — mauvaises configurations dans les Dockerfiles et docker-compose

Sévérités bloquantes : `CRITICAL`, `HIGH`

---

## 15. Variables d'environnement

Fichier `.env` monté dans les conteneurs `api` et `streamlit` via `env_file: .env`.

| Variable | Utilisée par | Description |
|---|---|---|
| `MONGO_CONNECTION_STRING` | Tous | URI de connexion MongoDB (`mongodb://...`) |
| `BSKY_USERNAME` | `ingest_from_bluesky` | Handle Bluesky (ex. `user.bsky.social`) |
| `BSKY_APP_PASSWORD` | `ingest_from_bluesky` | App password Bluesky (Settings > App passwords) |
| `OLLAMA_HOST` | `api` (docker-compose) | `http://ollama:11434` en Docker, `http://localhost:11434` en local |
| `OLLAMA_MODEL` | `api` (docker-compose) | `qwen2:1.5b` par défaut |
| `API_URL` | `streamlit` (docker-compose) | `http://api:8080/` en Docker, `http://localhost:8080/` en local |
| `GOOGLE_API_KEY` | `gemini_service.py` | Clé API Google Gemini (usage backup) |

---

## 16. Flux de données de bout en bout

```
┌─────────────────────────────────────────────────────────────────┐
│  INGESTION                                                      │
│                                                                 │
│  Bluesky API  ──atproto──►  fetch_from_keywords                 │
│  (4 thèmes, ~20 mots-clés, 25 posts/query, lang=en)            │
│                     │                                           │
│                     ▼                                           │
│             MongoDB · posts                                     │
└─────────────────────────────────────────────────────────────────┘
                      │ kedro run --pipeline=nlp_transform
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  NETTOYAGE NLP                                                  │
│                                                                 │
│  posts (bruts)  ──►  clean_text  ──►  normalize_text           │
│  (lowercase, URL, mention, hashtag, emoji, ponctuation,         │
│   NFKD, ASCII, whitespace)                                      │
│                     │                                           │
│                     ▼                                           │
│             MongoDB · cleaned_posts                             │
└─────────────────────────────────────────────────────────────────┘
                      │ kedro run --pipeline=vectorisation
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  VECTORISATION & CLASSIFICATION                                 │
│                                                                 │
│  cleaned_posts ──► TF-IDF (5000 features, sublinear_tf)        │
│                         ──► KMeans (k=2, random_state=42)      │
│                               │                                 │
│              ┌────────────────┤                                 │
│              │                │                                 │
│              ▼                ▼                                 │
│  MongoDB · classified_posts   data/06_models/                   │
│  (fake_news_prob, is_real,    tfidf_vectorizer.pkl              │
│   cluster, classified_at)     kmeans_model.pkl                  │
└─────────────────────────────────────────────────────────────────┘
                                │  modèles chargés au démarrage
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  API FASTAPI  (port 8080)                                       │
│                                                                 │
│  POST /ask?question=...                                         │
│    1. KMeansService.classify(text)                              │
│       → prétraitement identique nlp_transform                   │
│       → TF-IDF transform + KMeans predict                       │
│       → score = d0/(d0+d1) → verdict + probability             │
│    2. OllamaService.explain(claim, verdict, prob)               │
│       → POST http://ollama:11434/api/chat (qwen2:1.5b)          │
│       → explication linguistique 2-3 phrases                    │
│    3. VERDICT_COUNTER.inc()  [Prometheus]                       │
│    → { verdict, probability, based_on, cluster, explanation }   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STREAMLIT  (port 8501 → nginx :80)                             │
│                                                                 │
│  Onglet Fact-Check : chat → POST /ask → affichage verdict       │
│  Onglet Analytics  : dashboards corpus (Altair, MongoDB)        │
│  Onglet Energy     : rapport CodeCarbon (MongoDB energy_logs)   │
└─────────────────────────────────────────────────────────────────┘

Transversal :
  Kedro EnergyHook → CodeCarbon (avant/après chaque nœud)
                   → MongoDB · energy_logs
```

---

## 17. Démarrage rapide

### Prérequis

- Docker et Docker Compose v2
- Fichier `.env` rempli (voir §15)
- Connexion internet au premier démarrage (pull Ollama ~900 MB)

### Déploiement production (EC2)

Le déploiement est automatique via GitHub Actions à chaque push sur `main`. Manuellement :

```bash
# Sur l'instance EC2
cd ~/projet_etudes_data
git pull origin main
docker compose build
docker compose up -d --pull never
```

L'interface est accessible sur `http://<EC2_IP>/`.

| URL | Service |
|---|---|
| `http://<EC2_IP>/` | Streamlit (frontend) |
| `http://<EC2_IP>/airflow/` | Airflow UI |
| `http://<EC2_IP>/grafana/` | Grafana dashboards |

### Déploiement local (Docker)

```bash
make up
# équivalent : docker compose build --no-cache && docker compose up -d
```

L'interface est accessible sur `http://localhost/`.

### Exécution locale des pipelines

```bash
# 1. Installer les dépendances
make install-all   # uv sync --extra dev

# 2. Ingestion Bluesky
make run1          # kedro run --pipeline=ingest_from_bluesky

# 3. Nettoyage NLP
make run2          # kedro run --pipeline=nlp_transform

# 4. Vectorisation + classification + export artefacts
make run3          # kedro run --pipeline=vectorisation

# 5. Lancer API + Streamlit
make api           # uvicorn src.api.api:app --host 0.0.0.0 --port 8080
make web           # streamlit run src/streamlit_app/streamlit_app.py
```

### Ordre obligatoire

`run1` → `run2` → `run3` → API → Streamlit

L'API ne démarrera pas si `data/06_models/tfidf_vectorizer.pkl` et `kmeans_model.pkl` n'existent pas (erreur explicite au premier `/ask`).

### Arrêt

```bash
make down   # docker compose down -v  (supprime aussi les volumes)
```
