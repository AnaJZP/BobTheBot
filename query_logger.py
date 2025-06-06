import csv
import os
from datetime import datetime

LOG_FILE = 'consultas_bot.csv'
LOG_HEADER = ['timestamp', 'user_id', 'user_name', 'ticker', 'query_text', 'recommendation', 'justification']

def log_query(user_id: int, user_name: str, ticker: str, query_text: str, recommendation: str, justification: str):
    """Registra una consulta en el archivo CSV."""
    file_exists = os.path.isfile(LOG_FILE)
    
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists or os.path.getsize(LOG_FILE) == 0: # Escribir encabezado si el archivo es nuevo o vacío
                writer.writerow(LOG_HEADER)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([timestamp, user_id, user_name, ticker, query_text, recommendation, justification])
    except Exception as e:
        print(f"Error al escribir en el log: {e}")

if __name__ == '__main__':
    # Prueba de log
    log_query(12345, "test_user", "AAPL", "¿Compro AAPL?", "Compra", "PSAR cruzó hacia arriba.")
    log_query(67890, "another_user", "GOOG", "Opinión GOOG", "Mantener", "Indicadores neutrales.")
    print(f"Consultas de prueba registradas en {LOG_FILE}")