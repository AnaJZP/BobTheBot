"""Obtención de datos de mercado con yfinance, con caché en memoria."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300  # 5 minutos: evita repetir descargas de un mismo ticker
_cache: dict[tuple[str, str, str], tuple[float, "MarketData"]] = {}
_cache_lock = threading.Lock()


@dataclass
class MarketData:
    ticker: str
    history: pd.DataFrame      # OHLCV
    price: float               # precio más reciente
    currency: str | None


def get_market_data(ticker_symbol: str, period: str = "1y", interval: str = "1d") -> MarketData | None:
    """Descarga histórico y precio actual en una sola pasada (con caché de 5 min).

    Devuelve None si el ticker no existe o no hay datos suficientes.
    """
    key = (ticker_symbol, period, interval)
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_SECONDS:
            return hit[1]

    try:
        tk = yf.Ticker(ticker_symbol)
        hist = tk.history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        log.exception("Error descargando histórico de %s", ticker_symbol)
        return None

    if hist is None or hist.empty or not {"Open", "High", "Low", "Close"} <= set(hist.columns):
        log.info("Sin datos históricos para %s", ticker_symbol)
        return None
    hist = hist.dropna(subset=["High", "Low", "Close"])

    price, currency = None, None
    try:
        fi = tk.fast_info
        price = fi.get("last_price")
        currency = fi.get("currency")
    except Exception:
        log.debug("fast_info no disponible para %s", ticker_symbol)
    if price is None or pd.isna(price):
        price = hist["Close"].iloc[-1]

    data = MarketData(ticker_symbol, hist, float(price), currency)
    with _cache_lock:
        _cache[key] = (now, data)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for t in ("MSFT", "WALMEX.MX", "NOEXISTE123XYZ"):
        md = get_market_data(t)
        print(t, "->", None if md is None else f"{md.price:.2f} {md.currency} ({len(md.history)} filas)")
