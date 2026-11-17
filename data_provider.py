"""Obtención de datos de mercado (Yahoo Finance vía yfinance).

Si cambias de proveedor (Alpha Vantage, Bloomberg, Refinitiv...), solo se modifica
este archivo: el resto del bot no se entera.
"""
import logging

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)
COLUMNAS = ["Open", "High", "Low", "Close"]


def get_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame | None:
    """Datos históricos OHLC o None si no hay datos para el ticker."""
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        log.exception("Error al descargar %s", ticker)
        return None
    if hist.empty or not all(c in hist.columns for c in COLUMNAS):
        log.warning("Sin datos OHLC para %s (%s, %s)", ticker, period, interval)
        return None
    return hist


def get_quote(ticker: str, hist: pd.DataFrame | None = None) -> tuple[float | None, str]:
    """Precio más reciente y moneda (p. ej. 'USD' o 'MXN')."""
    precio, moneda = None, ""
    try:
        info = yf.Ticker(ticker).fast_info
        precio = info.get("last_price")
        moneda = info.get("currency") or ""
    except Exception:
        log.warning("fast_info no disponible para %s; uso el último cierre", ticker)
    if precio is None and hist is not None and not hist.empty:
        precio = hist["Close"].iloc[-1]
    return (float(precio) if precio is not None else None), moneda
