import pytest

from ticker_parser import extract_ticker


@pytest.mark.parametrize("texto, esperado", [
    ("¿Compro o vendo AMZN?", "AMZN"),
    ("Análisis de $nvda por favor", "NVDA"),
    ("¿Qué opinas de Tesla?", "TSLA"),
    ("¿Cómo ves a Walmex hoy?", "WALMEX.MX"),
    ("analiza gfnorteo.mx", "GFNORTEO.MX"),
    ("¿Cómo va el IPC?", "^MXX"),
    ("¿Qué tal BRK-B?", "BRK-B"),
    ("QUÉ OPINAS DE MSFT HOY", "MSFT"),
    ("hola, ¿cómo estás?", None),
])
def test_extract_ticker(texto, esperado):
    assert extract_ticker(texto) == esperado
