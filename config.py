# config.py
# El token NO se escribe aquí: se lee de la variable de entorno TELEGRAM_BOT_TOKEN
# o de un archivo .env en la raíz del proyecto con la línea TELEGRAM_BOT_TOKEN=<tu token>.
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Número de velas que se muestran en el gráfico (el periodo descargado depende de la
# ventana de tiempo elegida: ver TIMEFRAMES en data_provider.py)
CHART_BARS = int(os.getenv("BOB_CHART_BARS", "120"))
