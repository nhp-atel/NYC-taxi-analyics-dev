.PHONY: help install dev-install lint format test test-unit test-integration clean
.PHONY: producer pipeline api airflow terraform-init terraform-plan terraform-apply
.PHONY: download-sample docker-build docker-up docker-down

PYTHON := python3.11
PROJECT_ID := nyc-taxi-analytics-dev
REGION := us-central1

# Default target
help:
	@echo "NYC Taxi Analytics Platform - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install production dependencies"
	@echo "  dev-install      Install development dependencies"
	@echo "  pre-commit       Install pre-commit hooks"
	@echo ""
	@echo "Quality:"
	@echo "  lint             Run linters (ruff, mypy)"
	@echo "  format           Format code (black, ruff --fix)"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests"
	@echo ""
	@echo "Development:"
	@echo "  producer         Run producer locally (dry-run)"
	@echo "  pipeline         Run pipeline with DirectRunner"
	@echo "  api              Run FastAPI locally"
	@echo "  airflow          Start local Airflow"
	@echo ""
	@echo "Infrastructure:"
	@echo "  terraform-init   Initialize Terraform"
	@echo "  terraform-plan   Plan Terraform changes"
	@echo "  terraform-apply  Apply Terraform changes"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build all Docker images"
	@echo "  docker-up        Start all services"
	@echo "  docker-down      Stop all services"
	@echo ""
	@echo "Data:"
	@echo "  download-sample  Download sample NYC TLC data"

# Setup
install:
	$(PYTHON) -m pip install -e .

dev-install:
	$(PYTHON) -m pip install -e ".[dev]"

pre-commit:
	pre-commit install
	pre-commit install --hook-type pre-push

# Quality
lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Development
producer:
	$(PYTHON) -m src.producer.main --source data/yellow_tripdata_2024-01.parquet --dry-run --limit 100

producer-publish:
	$(PYTHON) -m src.producer.main --source data/sample.parquet --project $(PROJECT_ID) --topic trip-events --rate 100

pipeline:
	$(PYTHON) -m src.pipeline.main \
		--runner DirectRunner \
		--streaming \
		--project $(PROJECT_ID) \
		--input-subscription projects/$(PROJECT_ID)/subscriptions/dataflow-subscription \
		--output-table $(PROJECT_ID):nyc_taxi.clean_trips \
		--dlq-topic projects/$(PROJECT_ID)/topics/trip-events-dlq \
		--temp_location gs://$(PROJECT_ID)-temp/dataflow

pipeline-dataflow:
	$(PYTHON) -m src.pipeline.main \
		--runner DataflowRunner \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--input-subscription projects/$(PROJECT_ID)/subscriptions/dataflow-subscription \
		--output-table $(PROJECT_ID):nyc_taxi.clean_trips \
		--temp-location gs://$(PROJECT_ID)-temp/dataflow \
		--staging-location gs://$(PROJECT_ID)-temp/staging \
		--job-name nyc-taxi-pipeline \
		--max-num-workers 2 \
		--use-public-ips false

api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

airflow:
	cd docker && docker-compose up -d
	@echo "Airflow UI available at http://localhost:8080"
	@echo "Username: airflow, Password: airflow"

# Infrastructure
terraform-init:
	cd terraform/environments/dev && terraform init

terraform-plan:
	cd terraform/environments/dev && terraform plan -var-file=terraform.tfvars

terraform-apply:
	cd terraform/environments/dev && terraform apply -var-file=terraform.tfvars

terraform-destroy:
	cd terraform/environments/dev && terraform destroy -var-file=terraform.tfvars

# Docker
docker-build:
	docker build -t nyc-taxi-producer:latest -f docker/producer/Dockerfile .
	docker build -t nyc-taxi-api:latest -f docker/api/Dockerfile .

docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

# Data
download-sample:
	mkdir -p data
	curl -o data/yellow_tripdata_2024-01.parquet \
		https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
	curl -o data/taxi_zone_lookup.csv \
		https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
	@echo "Sample data downloaded to data/"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build dist .coverage htmlcov
