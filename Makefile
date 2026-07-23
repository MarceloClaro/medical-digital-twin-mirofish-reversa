.PHONY: install test lint typecheck build simulate
install:
	python -m pip install -e '.[dev]'
test:
	pytest
lint:
	ruff check .
typecheck:
	mypy src
build:
	python -m build
simulate:
	medical-twin examples/synthetic_case.json --seed 42 --horizon 4
