"""Main entrypoint for the NYC Taxi Dataflow pipeline."""

import json
import logging

import apache_beam as beam
from apache_beam.io import ReadFromPubSub, WriteToPubSub
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from src.pipeline.io import WriteToBigQueryClean, WriteToGCSRaw
from src.pipeline.options import TaxiPipelineOptions
from src.pipeline.transforms import DeduplicateByTripId, ParseTripEvent, ValidateTripEvent
from src.pipeline.transforms.validate import FilterInvalid, FilterValid


def run(argv=None, save_main_session=True):
    """Run the pipeline.

    Args:
        argv: Command line arguments
        save_main_session: Whether to save the main session
    """
    # Parse options
    pipeline_options = PipelineOptions(argv)
    taxi_options = pipeline_options.view_as(TaxiPipelineOptions)
    setup_options = pipeline_options.view_as(SetupOptions)
    setup_options.save_main_session = save_main_session

    logging.info(f"Input subscription: {taxi_options.input_subscription}")
    logging.info(f"Output table: {taxi_options.output_table}")
    logging.info(f"DLQ topic: {taxi_options.dlq_topic}")

    with beam.Pipeline(options=pipeline_options) as p:
        # Read from Pub/Sub
        raw_messages = (
            p
            | "ReadFromPubSub" >> ReadFromPubSub(
                subscription=taxi_options.input_subscription
            )
        )

        # Parse JSON to TripEvent
        parsed = raw_messages | "Parse" >> ParseTripEvent()

        # Route parse errors to DLQ
        _ = (
            parsed[ParseTripEvent.DLQ_TAG]
            | "FormatParseErrors" >> beam.Map(lambda x: json.dumps(x).encode("utf-8"))
            | "DLQParseErrors" >> WriteToPubSub(topic=taxi_options.dlq_topic)
        )

        # Validate parsed events
        validated = parsed[ParseTripEvent.VALID_TAG] | "Validate" >> ValidateTripEvent()

        # Split valid and invalid events
        valid_events = validated | "FilterValid" >> FilterValid()
        invalid_events = validated | "FilterInvalid" >> FilterInvalid()

        # Route invalid events to DLQ
        _ = (
            invalid_events
            | "FormatInvalidEvents" >> beam.Map(
                lambda ve: json.dumps({
                    "error": "validation_failed",
                    "errors": ve.validation.errors,
                    "event": ve.event.model_dump(mode="json"),
                }).encode("utf-8")
            )
            | "DLQInvalidEvents" >> WriteToPubSub(topic=taxi_options.dlq_topic)
        )

        # Deduplicate valid events
        deduped = (
            valid_events
            | "Deduplicate" >> DeduplicateByTripId(
                window_size_seconds=taxi_options.window_size_seconds,
                allowed_lateness_seconds=taxi_options.allowed_lateness_seconds,
            )
        )

        # Write to BigQuery
        _ = deduped | "WriteToBigQuery" >> WriteToBigQueryClean(
            table=taxi_options.output_table
        )

        # Optionally write raw events to GCS
        if taxi_options.raw_output_path:
            _ = deduped | "WriteToGCS" >> WriteToGCSRaw(
                output_path=taxi_options.raw_output_path
            )


def main():
    """Main entry point."""
    logging.getLogger().setLevel(logging.INFO)
    run()


if __name__ == "__main__":
    main()
