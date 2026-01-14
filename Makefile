.PHONY: requirements
requirements: ## Builds Python production requirements.
	venv/bin/python -m pip install "pip<25" "pip-tools<7.6" --upgrade --force-reinstall
	venv/bin/pip-compile \
		--allow-unsafe \
		--strip-extras \
		--upgrade \
		--output-file=requirements.txt \
		pyproject.toml

.PHONY: requirements-dev
requirements-dev: ## Builds Python development requirements.
	venv/bin/python -m pip install "pip<25" "pip-tools<7.6" --upgrade --force-reinstall
	venv/bin/pip-compile \
		--allow-unsafe \
		--strip-extras \
		--upgrade \
		--extra dev \
		--extra test \
		--output-file=requirements-dev.txt \
		pyproject.toml

.PHONY: requirements-all
requirements-all: requirements requirements-dev ## Builds all Python requirements files.


install-all:
	rm -rf venv
	python3 -m venv venv
	venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
	venv/bin/python -m spacy download en_core_web_sm


.PHONY: build db airflow-init up down logs
build:
	docker compose build --no-cache
db:
	docker compose up -d database
airflow-init:
	docker compose run --rm airflow-webserver airflow db init
	docker compose run --rm airflow-webserver airflow users create \
		--username admin \
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
	venv/bin/pre-commit run --all-files

.PHONY: run1
run1:
	kedro run --pipeline=ingest_from_bluesky

.PHONY: run2
run2:
	kedro run --pipeline=nlp_transform

.PHONY: run3
run3:
	kedro run --pipeline=vectorisation

.PHONY: web
web:
	streamlit run src/streamlit_app	/streamlit_app.py

.PHONY: api
api:
	uvicorn src.api.api:app --reload --port 8080
