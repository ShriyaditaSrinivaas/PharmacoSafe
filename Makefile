.PHONY: install pipeline generate train audit dashboard test clean

install:
	pip install -r requirements.txt

generate:
	python scripts/generate_data.py

train:
	python scripts/train_models.py

audit:
	python scripts/run_fairness_audit.py

pipeline: generate train audit

server:
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --cov=pharmacosafe --cov-report=term-missing

clean:
	rm -rf data/*.csv data/*.json models/*.joblib reports/ __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
