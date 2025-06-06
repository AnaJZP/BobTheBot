# data_provider.py
import yfinance as yf
import pandas as pd

def get_stock_data(ticker_symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame | None:
    """
    Obtiene datos históricos de un activo.

    Args:
        ticker_symbol (str): El símbolo del activo (ej. "AMZN", "TSLA").
        period (str): Periodo para datos históricos (ej. "1mo", "6mo", "1y").
        interval (str): Intervalo de los datos (ej. "1d", "1wk", "1h").

    Returns:
        pd.DataFrame | None: DataFrame con los datos históricos (OHLCV) o None si hay error.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # El propio yfinance maneja el log de errores si no encuentra el ticker o datos.
        hist_data = ticker.history(period=period, interval=interval)
        
        if hist_data.empty:
            print(f"Data Provider: No se encontraron datos históricos para {ticker_symbol} con período {period} e intervalo {interval}.")
            return None
            
        required_cols = ['Open', 'High', 'Low', 'Close'] # 'Volume' es importante pero a veces falta en algunos activos/intervalos muy cortos
        if not all(col in hist_data.columns for col in required_cols):
            print(f"Data Provider: Faltan columnas OHLCV en los datos de {ticker_symbol}. Columnas disponibles: {hist_data.columns.tolist()}")
            return None
            
        return hist_data
    except Exception as e:
        # yfinance a menudo ya imprime errores detallados.
        print(f"Data Provider: Excepción al obtener datos históricos para {ticker_symbol}: {e}")
        return None

def get_current_price(ticker_symbol: str) -> float | None:
    """
    Obtiene el precio más reciente de un activo.
    Intenta con fast_info.last_price, luego con history() del último día disponible.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Intento 1: Usar fast_info (puede ser más rápido pero a veces menos fiable)
        price = ticker.fast_info.get('last_price')

        # Intento 2: Si fast_info no da el precio, usar el cierre más reciente de history
        if price is None:
            # Pedimos 5 días por si el mercado estuvo cerrado o el último día no tiene datos aún
            hist = ticker.history(period="5d", interval="1d") 
            if not hist.empty and 'Close' in hist.columns:
                price = hist['Close'].iloc[-1]
            else:
                print(f"Data Provider: No se pudo obtener el precio actual de history para {ticker_symbol}.")
                return None
        
        if price is None:
            print(f"Data Provider: Precio final no encontrado para {ticker_symbol} después de varios intentos.")
            return None

        return float(price)
    except Exception as e:
        print(f"Data Provider: Excepción al obtener el precio actual para {ticker_symbol}: {e}")
        return None

if __name__ == '__main__':
    print("--- Probando get_stock_data ---")
    # Prueba con un ticker que debería funcionar
    datos_msft = get_stock_data("MSFT")
    if datos_msft is not None:
        print(f"\nDatos MSFT (últimos 5 días de {len(datos_msft)} filas):")
        print(datos_msft.tail())
    else:
        print("\nFallo al obtener datos de MSFT.")

    # Prueba con un ticker que podría dar problemas si los errores persisten
    datos_amzn = get_stock_data("AMZN")
    if datos_amzn is not None:
        print(f"\nDatos AMZN (últimos 5 días de {len(datos_amzn)} filas):")
        print(datos_amzn.tail())
    else:
        print("\nFallo al obtener datos de AMZN.")

    print("\n--- Probando get_current_price ---")
    precio_msft = get_current_price("MSFT")
    if precio_msft:
        print(f"\nPrecio actual MSFT: {precio_msft:.2f}")
    else:
        print("\nFallo al obtener precio actual de MSFT.")
        
    precio_tsla = get_current_price("TSLA")
    if precio_tsla:
        print(f"\nPrecio actual TSLA: {precio_tsla:.2f}")
    else:
        print("\nFallo al obtener precio actual de TSLA.")

    print("\n--- Probando con activo inexistente ---")
    datos_error = get_stock_data("ACTIVOSINEXISTENTE123XYZ")
    if datos_error is None:
        print("Prueba de activo inexistente (histórico) correcta (falló como se esperaba).")
    
    precio_error = get_current_price("ACTIVOSINEXISTENTE123XYZ")
    if precio_error is None:
        print("Prueba de activo inexistente (precio actual) correcta (falló como se esperaba).")