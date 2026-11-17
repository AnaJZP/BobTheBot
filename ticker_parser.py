"""Extracción de tickers desde mensajes en lenguaje natural."""
from __future__ import annotations

import re
import unicodedata

# Nombres comunes -> ticker de Yahoo Finance (claves sin acentos y en minúsculas)
COMPANY_ALIASES = {
    "apple": "AAPL", "tesla": "TSLA", "amazon": "AMZN", "microsoft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "facebook": "META",
    "netflix": "NFLX", "nvidia": "NVDA", "coca cola": "KO", "coca-cola": "KO",
    "cocacola": "KO", "pepsi": "PEP", "disney": "DIS", "intel": "INTC", "amd": "AMD",
    "walmart": "WMT", "mcdonalds": "MCD", "nike": "NKE", "boeing": "BA",
    "berkshire": "BRK-B", "jpmorgan": "JPM", "mastercard": "MA",
    "bitcoin": "BTC-USD", "btc": "BTC-USD", "ethereum": "ETH-USD", "eth": "ETH-USD",
    "oro": "GC=F", "petroleo": "CL=F",
    "s&p 500": "^GSPC", "s&p500": "^GSPC", "sp500": "^GSPC", "nasdaq": "^IXIC",
    "dow jones": "^DJI",
    # México (BMV)
    "walmex": "WALMEX.MX", "bimbo": "BIMBOA.MX", "cemex": "CEMEXCPO.MX",
    "america movil": "AMXB.MX", "femsa": "FEMSAUBD.MX", "banorte": "GFNORTEO.MX",
    "televisa": "TLEVISACPO.MX", "ipc": "^MXX", "dolar": "MXN=X", "peso": "MXN=X",
}

# Palabras que pueden aparecer en MAYÚSCULAS y no son tickers
STOPWORDS = {
    "A", "AL", "Y", "O", "DE", "DEL", "LA", "EL", "LOS", "LAS", "UN", "UNA", "EN", "ES",
    "QUE", "QUÉ", "COMO", "CÓMO", "VES", "VE", "HOY", "YA", "SI", "SÍ", "NO", "MI", "TU",
    "COMPRO", "VENDO", "COMPRAR", "VENDER", "OPINAS", "OPINION", "OPINIÓN", "ANALISIS",
    "ANÁLISIS", "ANALIZA", "ANALIZAR", "POR", "FAVOR", "PORFA", "PARA", "CON", "SOBRE",
    "HOLA", "BOB", "BOT", "GRACIAS", "TAL", "ESTA", "ESTÁ", "AHORA", "ACCION", "ACCIÓN",
    "ACCIONES", "PRECIO", "DIME", "DAME", "VS", "OK", "BUENO", "BIEN", "MAL",
}

_TICKER_RE = re.compile(r"^\^?[A-Z0-9]{1,10}(?:[.\-=][A-Z0-9]{1,6})?$")
_TOKEN_RE = re.compile(r"[\w.^=&\-]+")


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_ticker(raw: str) -> str | None:
    """Limpia y valida un ticker escrito por el usuario (ej. '$aapl' -> 'AAPL')."""
    t = raw.strip().lstrip("$").rstrip(".,;:!?").upper()
    return t if _TICKER_RE.match(t) and any(c.isalpha() for c in t) else None


def extract_ticker(text: str) -> str | None:
    """Intenta identificar el ticker en un mensaje.

    Orden de prioridad:
    1. Ticker explícito con $ (ej. "$AMZN")
    2. Nombre de empresa conocido (ej. "tesla", "coca cola", "bimbo")
    3. Palabra escrita en MAYÚSCULAS que no sea palabra común (ej. "¿Cómo ves GOOG?")
    4. Si el mensaje es una sola palabra, se toma como ticker (ej. "aapl")
    """
    if not text:
        return None

    m = re.search(r"\$([A-Za-z0-9.^=\-]+)", text)
    if m and (t := normalize_ticker(m.group(1))):
        return t

    plain = " " + _strip_accents(text.lower()) + " "
    for name in sorted(COMPANY_ALIASES, key=len, reverse=True):
        if re.search(rf"(?<![\w&]){re.escape(name)}(?![\w&])", plain):
            return COMPANY_ALIASES[name]

    tokens = [tok.strip(".-") for tok in _TOKEN_RE.findall(text)]
    for tok in tokens:
        if len(tok) >= 2 and tok.upper() == tok and tok.upper() not in STOPWORDS:
            if t := normalize_ticker(tok):
                return t

    if len(tokens) == 1 and tokens[0].upper() not in STOPWORDS:
        return normalize_ticker(tokens[0])
    return None
