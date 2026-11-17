"""Registro de consultas en CSV (logs/consultas_bot.csv, ignorado por Git).

El archivo contiene IDs y nombres de usuarios de Telegram: trátalo como dato
personal y no lo publiques en el repositorio.
"""
import csv
import logging
from datetime import datetime
from pathlib import Path

from config import LOG_FILE

log = logging.getLogger(__name__)
ENCABEZADO = ["timestamp", "user_id", "user_name", "ticker", "query_text",
              "recommendation", "justification"]


def log_query(user_id: int, user_name: str, ticker: str, query_text: str,
              recommendation: str, justification: str, archivo: Path = LOG_FILE) -> None:
    try:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not archivo.exists() or archivo.stat().st_size == 0
        with open(archivo, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if nuevo:
                w.writerow(ENCABEZADO)
            w.writerow([datetime.now().isoformat(timespec="seconds"), user_id, user_name,
                        ticker, query_text, recommendation, justification])
    except OSError:
        log.exception("No se pudo escribir el registro de consultas")
