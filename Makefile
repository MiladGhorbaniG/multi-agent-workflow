.PHONY: install test lint desk up

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check .
	ruff format --check .

desk:
	python -m booknook_flow.cli "Draft a short note about the four-book loan"

up:
	docker compose up --build
