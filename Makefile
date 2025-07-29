.PHONY: test lint format clean venv

test:
	pytest -q

coverage:
	pytest --cov=scripts --cov=tests

format:
	black scripts tests debugging run_pipeline.py

lint:
	flake8 scripts tests debugging run_pipeline.py

clean:
	rm -rf __pycache__ scripts/__pycache__ tests/__pycache__ .pytest_cache

venv:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt