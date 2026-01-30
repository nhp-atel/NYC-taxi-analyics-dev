"""CLI entrypoint for the event producer."""

import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.producer.config import ProducerSettings
from src.producer.data_loader import load_parquet_file, iter_trip_events
from src.producer.publisher import DryRunPublisher, TripEventPublisher
from src.producer.transformer import transform_event

app = typer.Typer(help="NYC Taxi Event Producer")
console = Console()


@app.command()
def main(
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help="Path to source parquet file",
    ),
    project: str = typer.Option(
        None,
        "--project",
        "-p",
        help="GCP project ID",
    ),
    topic: str = typer.Option(
        None,
        "--topic",
        "-t",
        help="Pub/Sub topic name",
    ),
    rate: float = typer.Option(
        100.0,
        "--rate",
        "-r",
        help="Messages per second",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of messages to publish",
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size",
        "-b",
        help="Batch size for publishing",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print messages instead of publishing",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Publish NYC taxi trip events to Pub/Sub."""
    # Load settings with CLI overrides
    settings = ProducerSettings()

    if source:
        settings.source_path = source
    if project:
        settings.project_id = project
    if topic:
        settings.topic_name = topic
    settings.rate_limit = rate
    settings.max_messages = limit
    settings.batch_size = batch_size
    settings.dry_run = dry_run
    settings.verbose = verbose

    console.print(f"[bold]NYC Taxi Event Producer[/bold]")
    console.print(f"Source: {settings.source_path}")
    console.print(f"Topic: {settings.topic_path}")
    console.print(f"Rate: {settings.rate_limit} msg/s")
    if settings.max_messages:
        console.print(f"Limit: {settings.max_messages} messages")
    if settings.dry_run:
        console.print("[yellow]DRY RUN MODE - no messages will be published[/yellow]")
    console.print()

    # Load data
    try:
        console.print("Loading data...")
        df = load_parquet_file(settings.source_path)
        total_rows = len(df)
        console.print(f"Loaded {total_rows:,} rows")
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading data: {e}[/red]")
        sys.exit(1)

    # Initialize publisher
    if settings.dry_run:
        publisher = DryRunPublisher(verbose=settings.verbose)
    else:
        publisher = TripEventPublisher(
            project_id=settings.project_id,
            topic_name=settings.topic_name,
            rate_limit=settings.rate_limit,
            batch_size=settings.batch_size,
        )

    # Process and publish events
    max_events = settings.max_messages or total_rows
    start_time = time.time()
    transformed_count = 0
    skipped_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Publishing events...", total=max_events)

        for raw_event in iter_trip_events(df, limit=max_events):
            event = transform_event(raw_event)

            if event is None:
                skipped_count += 1
                continue

            publisher.publish(event)
            transformed_count += 1
            progress.update(task, advance=1)

            # Periodic stats
            if transformed_count % 1000 == 0 and settings.verbose:
                stats = publisher.stats
                console.print(
                    f"  Published: {stats['published']:,}, "
                    f"Errors: {stats['errors']:,}"
                )

    # Flush remaining messages
    console.print("Flushing remaining messages...")
    publisher.flush()
    publisher.close()

    # Final stats
    elapsed = time.time() - start_time
    stats = publisher.stats

    console.print()
    console.print("[bold green]Complete![/bold green]")
    console.print(f"  Transformed: {transformed_count:,}")
    console.print(f"  Published: {stats['published']:,}")
    console.print(f"  Skipped: {skipped_count:,}")
    console.print(f"  Errors: {stats['errors']:,}")
    console.print(f"  Duration: {elapsed:.1f}s")
    console.print(f"  Rate: {stats['published'] / elapsed:.1f} msg/s")


if __name__ == "__main__":
    app()
