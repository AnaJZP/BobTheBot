"""Configuración del bot.

El token NUNCA se escribe en este archivo: se lee de la variable de entorno
TELEGRAM_BOT_TOKEN o de un archivo .env en la raíz del proyecto (ignorado por Git).
Copia .env.example como .env y pega ahí tu token de @BotFather.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Parámetros del análisis (modifícalos aquí, no dentro de la lógica)
PERIODO_DATOS = os.getenv("PERIODO_DATOS", "1y")
INTERVALO_DATOS = os.getenv("INTERVALO_DATOS", "1d")
DIAS_GRAFICA = int(os.getenv("DIAS_GRAFICA", "100"))
ENVIAR_GRAFICA = os.getenv("ENVIAR_GRAFICA", "1") == "1"

# Registro de consultas (contiene IDs de usuarios de Telegram: no se sube al repo)
LOG_FILE = Path(os.getenv("LOG_FILE", BASE_DIR / "logs" / "consultas_bot.csv"))


def get_token() -> str:
    """Devuelve el token o termina con un mensaje claro si no está configurado."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token.startswith("pega_aqui"):
        raise SystemExit(
            "\n[ERROR] No encontré TELEGRAM_BOT_TOKEN.\n"
            "  1) Copia .env.example como .env\n"
            "  2) Pega el token que te dio @BotFather\n"
            "  3) Vuelve a ejecutar: python main.py\n"
        )
    return token
