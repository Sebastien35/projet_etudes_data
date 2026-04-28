.PHONY: lock
lock: ## Generate/update uv.lock from pyproject.toml.
	uv lock

.PHONY: lock-upgrade
lock-upgrade: ## Upgrade all dependencies and regenerate uv.lock.
	uv lock --upgrade


install-all:
	uv sync --extra dev


.PHONY: build db airflow-init up down logs
build:
	docker compose build --no-cache
db:
	docker compose up -d database
airflow-init:
	docker compose run --rm airflow-webserver airflow db init
	docker compose run --rm airflow-webserver airflow users create \
		--username admin \
		--password admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com
up: build airflow-init
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f
# run:
# 	streamlit run src/streamlit/app.py

lint:
	uv run pre-commit run --all-files

.PHONY: run1
run1:
	PYTHONPATH=. PYTHONWARNINGS="default:Kedro is not yet fully compatible" kedro run --pipeline=ingest_from_bluesky

.PHONY: run2
run2:
	PYTHONPATH=. PYTHONWARNINGS="default:Kedro is not yet fully compatible" kedro run --pipeline=nlp_transform

.PHONY: run3
run3:
	PYTHONPATH=. PYTHONWARNINGS="default:Kedro is not yet fully compatible" kedro run --pipeline=vectorisation

.PHONY: run4
run4:
	PYTHONPATH=. PYTHONWARNINGS="default:Kedro is not yet fully compatible" kedro run --pipeline=emotion_classification

.PHONY: web
web:
	PYTHONPATH=. streamlit run src/streamlit_app/streamlit_app.py

.PHONY: api
api:
	PYTHONPATH=. uvicorn src.api.api:app --host 0.0.0.0 --port 8080

.PHONY: quickstart
quickstart: install-all run3 web api

.PHONY: startapp
startapp:
	web api