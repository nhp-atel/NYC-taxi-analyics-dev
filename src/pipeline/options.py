"""Pipeline options configuration."""

from apache_beam.options.pipeline_options import PipelineOptions


class TaxiPipelineOptions(PipelineOptions):
    """Custom options for the NYC Taxi pipeline."""

    @classmethod
    def _add_argparse_args(cls, parser) -> None:
        """Add custom pipeline arguments."""
        parser.add_argument(
            "--input-subscription",
            dest="input_subscription",
            required=True,
            help="Pub/Sub subscription to read from",
        )
        parser.add_argument(
            "--output-table",
            dest="output_table",
            required=True,
            help="BigQuery table to write to (project:dataset.table)",
        )
        parser.add_argument(
            "--dlq-topic",
            dest="dlq_topic",
            required=True,
            help="Pub/Sub topic for dead letter queue",
        )
        parser.add_argument(
            "--raw-output-path",
            dest="raw_output_path",
            default=None,
            help="GCS path for raw event archives (optional)",
        )
        parser.add_argument(
            "--window-size-seconds",
            dest="window_size_seconds",
            type=int,
            default=86400,  # 24 hours
            help="Window size in seconds for deduplication",
        )
        parser.add_argument(
            "--allowed-lateness-seconds",
            dest="allowed_lateness_seconds",
            type=int,
            default=21600,  # 6 hours
            help="Allowed lateness in seconds for late data",
        )
