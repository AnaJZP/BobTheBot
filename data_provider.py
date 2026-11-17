"""Obtención de datos de mercado con yfinance, con caché en memoria."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

# Ventanas de tiempo disponibles: etiqueta -> (periodo a descargar, intervalo de Yahoo, horas por vela)
# Yahoo no ofrece velas de 4 h: se construyen agrupando velas de 1 h.
TIMEFRAMES = {
    "1h": ("60d", "1h", 1),
    "4h": ("200d", "1h", 4),
    "1d": ("1y", "1d", None),
}
TIMEFRAME_LABELS = {"1h": "1 hora", "4h": "4 horas", "1d": "1 día"}
DEFAULT_TIMEFRAME = "1d"

CACHE_TTL_SECONDS = 300  # 5 minutos: evita repetir descargas de un mismo ticker
_cache: dict[tuple[str, str], tuple[float, "MarketData"]] = {}
_cache_lock = threading.Lock()


@dataclass
class MarketData:
    ticker: str
    timeframe: str
    history: pd.DataFrame      # OHLCV
    price: float               # precio más reciente
    currency: str | None


def resample_hours(df: pd.DataFrame, hours: int) -> pd.DataFrame:
    """Agrupa velas de 1 h en velas de `hours` horas dentro de cada sesión.

    Se agrupa por día y por bloques de `hours` velas consecutivas, así las velas no
    cruzan cierres de mercado ni fines de semana (funciona igual para cripto 24/7).
    """
    day = df.index.normalize()
    block = df.groupby(day).cumcount() // hours
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    if "Volume" in df.columns:
        agg["Volume"] = "sum"
    grouped = df.groupby([day, block])
    out = grouped.agg(agg)
    out.index = grouped.apply(lambda g: g.index[0])
    return out


def get_market_data(ticker_symbol: str, timeframe: str = DEFAULT_TIMEFRAME) -> MarketData | None:
    """Descarga histórico y precio actual en una sola pasada (con caché de 5 min).

    Devuelve None si el ticker no existe o no hay datos.
    """
    if timeframe not in TIMEFRAMES:
        timeframe = DEFAULT_TIMEFRAME
    key = (ticker_symbol, timeframe)
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_SECONDS:
            return hit[1]

    period, interval, hours = TIMEFRAMES[timeframe]
    try:
        tk = yf.Ticker(ticker_symbol)
        hist = tk.history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        log.exception("Error descargando histórico de %s", ticker_symbol)
        return None

    if hist is None or hist.empty or not {"Open", "High", "Low", "Close"} <= set(hist.columns):
        log.info("Sin datos históricos para %s (%s)", ticker_symbol, timeframe)
        return None
    hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
    if hours and hours > 1:
        hist = resample_hours(hist, hours)

    price, currency = None, None
    try:
        fi = tk.fast_info
        price = fi.get("last_price")
        currency = fi.get("currency")
    except Exception:
        log.debug("fast_info no disponible para %s", ticker_symbol)
    if price is None or pd.isna(price):
        price = hist["Close"].iloc[-1]

    data = MarketData(ticker_symbol, timeframe, hist, float(price), currency)
    with _cache_lock:
        _cache[key] = (now, data)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for t in ("MSFT", "WALMEX.MX", "NOEXISTE123XYZ"):
        for tf in TIMEFRAMES:
            md = get_market_data(t, tf)
            print(t, tf, "->", None if md is None else f"{md.price:.2f} {md.currency} ({len(md.history)} velas)")
