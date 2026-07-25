"""Simple container-friendly scheduled ingestion entry point."""
import os
import time
from .ingestion import ingest


def main() -> None:
    interval = int(os.getenv("INGEST_INTERVAL_SECONDS", "21600"))
    while True:
        try:
            print(f"Ingested {ingest()} recipes", flush=True)
        except Exception as error:
            print(f"Ingestion failed: {error}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
