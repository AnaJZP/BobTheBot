"""Registro de consultas en CSV (seguro para llamadas concurrentes)."""
from __future__ import annotations

import csv
import logging
import threading
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).with_name("consultas_bot.csv")
LOG_HEADER = ["timestamp", "user_id", "user_name", "ticker", "query_text", "recommendation", "justification"]

_lock = threading.Lock()
log = logging.getLogger(__name__)


def log_query(user_id: int, user_name: str, ticker: str, query_text: str,
              recommendation: str, justification: str) -> None:
    """Agrega una fila al CSV de consultas."""
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, user_name, ticker,
           query_text, recommendation, justification]
    try:
        with _lock:
            new_file = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0
            with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if new_file:
                    writer.writerow(LOG_HEADER)
                writer.writerow(row)
    except OSError:
        log.exception("No se pudo escribir en %s", LOG_FILE)
