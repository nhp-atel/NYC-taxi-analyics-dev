# NYC Taxi Analytics Platform

A real-time analytics platform demonstrating data engineering skills using GCP managed services and NYC TLC public trip data.

## Architecture

```
NYC TLC Parquet → Python Producer → Pub/Sub → Dataflow/Beam → GCS Raw + BigQuery Clean
                                                                      ↓
                                              FastAPI (Cloud Run) ← Airflow → BigQuery Curated
```

## Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Terraform 1.0+
- Docker & Docker Compose
- GCP account with billing enabled

## Quick Start

```bash
# Install dependencies
make dev-install
make pre-commit

# Download sample data
make download-sample

# Run producer in dry-run mode
make producer

# Run pipeline with DirectRunner
make pipeline

# Start local Airflow
make airflow

# Run API locally
make api
```

## GCP Setup

1. Create GCP project: `nyc-taxi-analytics-dev`
2. Enable required APIs:
   ```bash
   gcloud services enable \
     pubsub.googleapis.com \
     dataflow.googleapis.com \
     bigquery.googleapis.com \
     storage.googleapis.com \
     run.googleapis.com \
     cloudbuild.googleapis.com
   ```
3. Initialize Terraform:
   ```bash
   make terraform-init
   make terraform-plan
   make terraform-apply
   ```

## Project Structure

```
nyc-taxi-analytics/
├── src/
│   ├── producer/      # Event producer (Pub/Sub publisher)
│   ├── pipeline/      # Dataflow/Beam streaming pipeline
│   ├── dags/          # Airflow DAGs for orchestration
│   ├── api/           # FastAPI REST API
│   └── shared/        # Shared schemas and utilities
├── terraform/         # Infrastructure as Code
├── tests/             # Unit, integration, and E2E tests
├── docker/            # Docker configurations
└── scripts/           # Helper scripts
```

## Data Source

NYC TLC Trip Record Data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

## License

MIT
