.PHONY: test lint format clean venv

test:
	pytest -q

coverage:
	pytest --cov=scripts --cov=tests

clean:
	rm -rf __pycache__ scripts/__pycache__ tests/__pycache__ utils/__pycache__ .pytest_cache

venv:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt