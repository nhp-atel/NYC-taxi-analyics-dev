# BigQuery dataset
resource "google_bigquery_dataset" "nyc_taxi" {
  dataset_id    = "nyc_taxi"
  friendly_name = "NYC Taxi Analytics"
  description   = "NYC TLC trip data analytics dataset"
  location      = var.region
  project       = var.project_id

  # Default table expiration: none (keep data indefinitely)
  # default_table_expiration_ms = null

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
  }
}

# Clean trips fact table (populated by Dataflow)
resource "google_bigquery_table" "clean_trips" {
  dataset_id          = google_bigquery_dataset.nyc_taxi.dataset_id
  table_id            = "clean_trips"
  project             = var.project_id
  deletion_protection = false # Set to true in production

  time_partitioning {
    type  = "DAY"
    field = "pickup_date"
  }

  clustering = ["pickup_location_id", "dropoff_location_id"]

  require_partition_filter = true

  schema = jsonencode([
    {
      name        = "trip_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Deterministic SHA256 hash for deduplication"
    },
    {
      name        = "pickup_datetime"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Trip pickup timestamp"
    },
    {
      name        = "dropoff_datetime"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Trip dropoff timestamp"
    },
    {
      name        = "pickup_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Partition key derived from pickup_datetime"
    },
    {
      name        = "pickup_location_id"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "NYC TLC zone ID for pickup"
    },
    {
      name        = "dropoff_location_id"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "NYC TLC zone ID for dropoff"
    },
    {
      name        = "vendor_id"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "Taxi vendor ID"
    },
    {
      name        = "passenger_count"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "Number of passengers"
    },
    {
      name        = "trip_distance"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Trip distance in miles"
    },
    {
      name        = "fare_amount"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Base fare amount"
    },
    {
      name        = "tip_amount"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Tip amount"
    },
    {
      name        = "total_amount"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Total trip amount"
    },
    {
      name        = "payment_type"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "Payment type code"
    },
    {
      name        = "ingestion_timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "When the record was ingested"
    }
  ])

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    layer       = "clean"
  }
}

# Zone dimension table
resource "google_bigquery_table" "dim_zones" {
  dataset_id          = google_bigquery_dataset.nyc_taxi.dataset_id
  table_id            = "dim_zones"
  project             = var.project_id
  deletion_protection = false

  schema = jsonencode([
    {
      name        = "zone_id"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "NYC TLC zone ID"
    },
    {
      name        = "borough"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "NYC borough name"
    },
    {
      name        = "zone_name"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Zone name"
    },
    {
      name        = "service_zone"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Service zone category"
    }
  ])

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    layer       = "dimension"
  }
}

# Daily zone stats mart (populated by Airflow)
resource "google_bigquery_table" "dm_daily_zone_stats" {
  dataset_id          = google_bigquery_dataset.nyc_taxi.dataset_id
  table_id            = "dm_daily_zone_stats"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "stat_date"
  }

  clustering = ["zone_id"]

  require_partition_filter = true

  schema = jsonencode([
    {
      name        = "stat_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Statistics date"
    },
    {
      name        = "zone_id"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "NYC TLC zone ID"
    },
    {
      name        = "trip_count"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "Total trips from this zone"
    },
    {
      name        = "total_passengers"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "Total passengers"
    },
    {
      name        = "total_distance"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Total trip distance in miles"
    },
    {
      name        = "total_fare"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Total fare amount"
    },
    {
      name        = "total_tip"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Total tip amount"
    },
    {
      name        = "total_revenue"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Total revenue (total_amount)"
    },
    {
      name        = "avg_fare"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Average fare per trip"
    },
    {
      name        = "avg_distance"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Average trip distance"
    },
    {
      name        = "avg_tip_pct"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Average tip percentage"
    },
    {
      name        = "updated_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Last update timestamp"
    }
  ])

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    layer       = "mart"
  }
}

# Hourly patterns mart
resource "google_bigquery_table" "dm_hourly_patterns" {
  dataset_id          = google_bigquery_dataset.nyc_taxi.dataset_id
  table_id            = "dm_hourly_patterns"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "stat_date"
  }

  clustering = ["pickup_location_id", "hour_of_day"]

  require_partition_filter = true

  schema = jsonencode([
    {
      name        = "stat_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Statistics date"
    },
    {
      name        = "hour_of_day"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "Hour (0-23)"
    },
    {
      name        = "day_of_week"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "Day of week (1=Sunday, 7=Saturday)"
    },
    {
      name        = "pickup_location_id"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "NYC TLC zone ID"
    },
    {
      name        = "trip_count"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "Number of trips"
    },
    {
      name        = "avg_fare"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Average fare"
    },
    {
      name        = "avg_trip_duration_minutes"
      type        = "FLOAT64"
      mode        = "NULLABLE"
      description = "Average trip duration in minutes"
    },
    {
      name        = "updated_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Last update timestamp"
    }
  ])

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    layer       = "mart"
  }
}

# IAM bindings
resource "google_bigquery_dataset_iam_member" "dataflow_editor" {
  dataset_id = google_bigquery_dataset.nyc_taxi.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${var.dataflow_service_account}"
}

resource "google_bigquery_dataset_iam_member" "api_viewer" {
  dataset_id = google_bigquery_dataset.nyc_taxi.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${var.api_service_account}"
}
