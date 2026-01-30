#!/bin/bash
# Deploy Dataflow pipeline

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-nyc-taxi-analytics-dev}"
REGION="${REGION:-us-central1}"
TEMP_BUCKET="${PROJECT_ID}-temp"
JOB_NAME="${JOB_NAME:-nyc-taxi-pipeline}"

echo "=== Deploying Dataflow Pipeline ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Job Name: $JOB_NAME"
echo

# Check if running streaming or batch
MODE="${1:-streaming}"

if [ "$MODE" == "streaming" ]; then
    echo "Deploying streaming pipeline..."

    python -m src.pipeline.main \
        --runner DataflowRunner \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --input-subscription "projects/$PROJECT_ID/subscriptions/dataflow-subscription" \
        --output-table "$PROJECT_ID:nyc_taxi.clean_trips" \
        --dlq-topic "projects/$PROJECT_ID/topics/trip-events-dlq" \
        --temp-location "gs://$TEMP_BUCKET/temp" \
        --staging-location "gs://$TEMP_BUCKET/staging" \
        --job-name "$JOB_NAME" \
        --max-num-workers 2 \
        --machine-type n1-standard-2 \
        --service-account-email "taxi-dataflow@$PROJECT_ID.iam.gserviceaccount.com" \
        --enable-streaming-engine \
        --streaming

elif [ "$MODE" == "batch" ]; then
    echo "Deploying batch pipeline with FlexRS (70% cost savings)..."

    python -m src.pipeline.main \
        --runner DataflowRunner \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --input-subscription "projects/$PROJECT_ID/subscriptions/dataflow-subscription" \
        --output-table "$PROJECT_ID:nyc_taxi.clean_trips" \
        --dlq-topic "projects/$PROJECT_ID/topics/trip-events-dlq" \
        --temp-location "gs://$TEMP_BUCKET/temp" \
        --staging-location "gs://$TEMP_BUCKET/staging" \
        --job-name "$JOB_NAME" \
        --max-num-workers 2 \
        --machine-type n1-standard-2 \
        --service-account-email "taxi-dataflow@$PROJECT_ID.iam.gserviceaccount.com" \
        --flexrs-goal=COST_OPTIMIZED

elif [ "$MODE" == "direct" ]; then
    echo "Running with DirectRunner (local)..."

    python -m src.pipeline.main \
        --runner DirectRunner \
        --project "$PROJECT_ID" \
        --input-subscription "projects/$PROJECT_ID/subscriptions/dataflow-subscription" \
        --output-table "$PROJECT_ID:nyc_taxi.clean_trips" \
        --dlq-topic "projects/$PROJECT_ID/topics/trip-events-dlq" \
        --temp-location "gs://$TEMP_BUCKET/temp"

else
    echo "Usage: $0 [streaming|batch|direct]"
    exit 1
fi

echo
echo "=== Deployment Complete ==="
echo "Monitor at: https://console.cloud.google.com/dataflow/jobs?project=$PROJECT_ID"
