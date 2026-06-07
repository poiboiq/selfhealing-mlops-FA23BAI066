import os
import time
import requests
from prometheus_client import Gauge, start_http_server

APP_URL = os.getenv("APP_URL", "http://127.0.0.1:32500").rstrip("/")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "8000"))
POLL_INTERVAL_SECONDS = 5

prediction_confidence_score = Gauge(
    "prediction_confidence_score",
    "Latest confidence score returned by the Sentiment API."
)

def read_latest_confidence() -> float:
    try:
        response = requests.get(f"{APP_URL}/api/latest-confidence", timeout=3)
        response.raise_for_status()
        value = float(response.json().get("confidence", 1.0))
        if 0.0 <= value <= 1.0:
            return value
    except Exception:
        pass
    return 1.0

def main() -> None:
    start_http_server(EXPORTER_PORT)
    while True:
        prediction_confidence_score.set(read_latest_confidence())
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
