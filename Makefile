.PHONY: install check lint test build schema ci-docker

install:
	uv sync

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/mypy src

test:
	.venv/bin/pytest --cov=study_extract --cov-report=term-missing

schema:
	.venv/bin/study-extract schema --output schemas/extraction.schema.json
	.venv/bin/study-extract catalog --output schemas/fields.json

build:
	.venv/bin/python -m build --no-isolation

check: lint test build

ci-docker:
	COPYFILE_DISABLE=1 tar --exclude='__pycache__' -cf - src tests pyproject.toml README.md LICENSE | docker run --rm -i -w /tmp/check python:3.13-slim sh -c 'tar -xf - && pip install uv && uv sync && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy src && .venv/bin/pytest && .venv/bin/python -m build --no-isolation'
