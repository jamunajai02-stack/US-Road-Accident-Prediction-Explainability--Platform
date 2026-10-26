.PHONY: help install lint test train dev-up dev-down demo clean

PYTHON ?= python

help:
	@echo "US Road Accident Prediction & Explainability Platform"
	@echo "Available commands:"
	@echo "  make install     Install production & development dependencies"
	@echo "  make lint        Run ruff formatting & mypy type checks"
	@echo "  make test        Execute full pytest suite across all modules"
	@echo "  make train       Run Phase 3 STGCN model training & export"
	@echo "  make demo        Run Phase 5 live end-to-end simulation"
	@echo "  make dev-up      Spin up Docker Compose environment (PostGIS, Redis, Kafka, API)"
	@echo "  make dev-down    Tear down Docker Compose containers"
	@echo "  make clean       Remove temporary build and cache artifacts"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,geo,kafka,db]"

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy libs modules services

test:
	$(PYTHON) -m unittest discover -s tests/unit -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase0_5_graph_extraction/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase1_data_infra/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase2_graph_construction/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase3_predictive_core/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase4_explainability/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s modules/phase5_realtime_service/tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s services/api_gateway/tests -p "test_*.py"

train:
	$(PYTHON) scripts/run_phase3_train.py --epochs 15

demo:
	$(PYTHON) scripts/run_phase5_live_demo.py

dev-up:
	docker compose up -d

dev-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
