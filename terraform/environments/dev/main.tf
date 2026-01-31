terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # For production, use remote backend
  # backend "gcs" {
  #   bucket = "nyc-taxi-analytics-tf-state"
  #   prefix = "terraform/state/dev"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# IAM module - creates service accounts
module "iam" {
  source = "../../modules/iam"

  project_id = var.project_id
}

# Pub/Sub module - creates topics and subscriptions
module "pubsub" {
  source = "../../modules/pubsub"

  project_id               = var.project_id
  producer_service_account = module.iam.producer_service_account_email
  dataflow_service_account = module.iam.dataflow_service_account_email

  depends_on = [module.iam]
}

# GCS module - creates storage buckets
module "gcs" {
  source = "../../modules/gcs"

  project_id               = var.project_id
  region                   = var.region
  dataflow_service_account = module.iam.dataflow_service_account_email

  depends_on = [module.iam]
}

# BigQuery module - creates dataset and tables
module "bigquery" {
  source = "../../modules/bigquery"

  project_id               = var.project_id
  region                   = var.region
  dataflow_service_account = module.iam.dataflow_service_account_email
  api_service_account      = module.iam.api_service_account_email

  depends_on = [module.iam]
}

# Dataflow module - job configuration
module "dataflow" {
  source = "../../modules/dataflow"

  project_id               = var.project_id
  region                   = var.region
  dataflow_service_account = module.iam.dataflow_service_account_email
  temp_bucket              = module.gcs.temp_bucket_name
  input_subscription       = module.pubsub.dataflow_subscription_id
  output_table             = module.bigquery.clean_trips_table_id
  dlq_topic                = module.pubsub.dlq_topic_id

  depends_on = [module.gcs, module.pubsub, module.bigquery]
}

# Cloud Run module - API deployment
module "cloudrun" {
  source = "../../modules/cloudrun"

  project_id          = var.project_id
  region              = var.region
  api_service_account = module.iam.api_service_account_email
  bq_dataset          = module.bigquery.dataset_id

  depends_on = [module.bigquery, module.iam]
}
