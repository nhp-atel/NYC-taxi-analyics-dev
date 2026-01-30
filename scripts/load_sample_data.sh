#!/bin/bash
# Load sample data and publish events

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-nyc-taxi-analytics-dev}"
DATA_DIR="data"
SAMPLE_FILE="$DATA_DIR/yellow_tripdata_2024-01.parquet"

echo "=== Loading Sample Data ==="
echo

# Download sample data if needed
if [ ! -f "$SAMPLE_FILE" ]; then
    echo "Downloading sample data..."
    mkdir -p "$DATA_DIR"
    curl -o "$SAMPLE_FILE" \
        https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
    echo "✓ Downloaded sample data"
else
    echo "✓ Sample data already exists"
fi

# Download zone lookup if needed
ZONE_FILE="$DATA_DIR/taxi_zone_lookup.csv"
if [ ! -f "$ZONE_FILE" ]; then
    echo "Downloading zone lookup..."
    curl -o "$ZONE_FILE" \
        https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
    echo "✓ Downloaded zone lookup"
else
    echo "✓ Zone lookup already exists"
fi

echo
echo "Sample data ready!"
echo

# Ask user what to do
echo "Options:"
echo "  1. Dry run (print events without publishing)"
echo "  2. Publish 1000 events to Pub/Sub"
echo "  3. Publish 10000 events to Pub/Sub"
echo "  4. Exit"
echo

read -p "Select option [1-4]: " option

case $option in
    1)
        echo "Running dry run..."
        python -m src.producer.main \
            --source "$SAMPLE_FILE" \
            --dry-run \
            --limit 100
        ;;
    2)
        echo "Publishing 1000 events..."
        python -m src.producer.main \
            --source "$SAMPLE_FILE" \
            --project "$PROJECT_ID" \
            --topic trip-events \
            --limit 1000 \
            --rate 100
        ;;
    3)
        echo "Publishing 10000 events..."
        python -m src.producer.main \
            --source "$SAMPLE_FILE" \
            --project "$PROJECT_ID" \
            --topic trip-events \
            --limit 10000 \
            --rate 500
        ;;
    4)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo
echo "=== Complete ==="
