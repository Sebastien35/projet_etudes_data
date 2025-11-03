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

# run:
# 	streamlit run src/streamlit/app.py


