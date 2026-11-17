"""Identificación de tickers en mensajes en lenguaje natural."""
import re
import unicodedata

# Nombres comunes -> ticker de Yahoo Finance (amplía esta lista libremente)
ALIAS = {
    "apple": "AAPL", "tesla": "TSLA", "amazon": "AMZN", "microsoft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "netflix": "NFLX", "nvidia": "NVDA",
    "meta": "META", "facebook": "META", "coca cola": "KO", "coca-cola": "KO",
    "walmart de mexico": "WALMEX.MX", "walmex": "WALMEX.MX", "bimbo": "BIMBOA.MX",
    "cemex": "CEMEXCPO.MX", "femsa": "FEMSAUBD.MX", "banorte": "GFNORTEO.MX",
    "america movil": "AMXB.MX", "grupo mexico": "GMEXICOB.MX",
    "ipc": "^MXX", "s&p 500": "^GSPC", "sp500": "^GSPC", "bitcoin": "BTC-USD",
}

# Palabras en mayúsculas que NO son tickers
NO_TICKERS = {
    "HOY", "COMPRO", "VENDO", "OPINAS", "ANALISIS", "QUE", "DE", "LA", "EL", "LOS",
    "LAS", "Y", "O", "EN", "POR", "FAVOR", "COMO", "VES", "TAL", "ME", "MI", "UN",
    "UNA", "ES", "SI", "NO", "AL", "DEL", "PARA", "CON", "BOB", "OK", "HOLA",
    "ACCION", "ACCIONES", "PRECIO", "AYUDA", "USD", "MXN",
}

_DOLAR = re.compile(r"\$([A-Za-z\^][A-Za-z0-9\-]{0,9}(?:\.[A-Za-z]{1,3})?)")
_SUFIJO = re.compile(r"\b([A-Za-z][A-Za-z0-9]{0,11}\.(?:MX|mx|Mx))\b")
_MAYUS = re.compile(r"(?<![\w^])(\^?[A-Z][A-Z0-9]{0,9}(?:[.\-][A-Z]{1,3})?)(?![\w])")


def _normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_acentos.lower()


def extract_ticker(texto: str) -> str | None:
    """Devuelve el ticker más probable o None.

    Prioridad: $TICKER  >  emisora con sufijo .MX  >  nombre conocido  >  palabra en MAYÚSCULAS.
    """
    if m := _DOLAR.search(texto):
        return m.group(1).upper()
    if m := _SUFIJO.search(texto):
        return m.group(1).upper()

    normal = _normalizar(texto)
    for nombre in sorted(ALIAS, key=len, reverse=True):   # primero los nombres largos
        if re.search(rf"(?<![a-z]){re.escape(nombre)}(?![a-z])", normal):
            return ALIAS[nombre]

    candidatos = [c for c in _MAYUS.findall(texto)
                  if _normalizar(c).upper() not in NO_TICKERS and len(c.strip("^")) > 1]
    return candidatos[-1] if candidatos else None
