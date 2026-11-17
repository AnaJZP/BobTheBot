import numpy as np
import pandas as pd

from technical_analysis import COMPRA, MANTENER, VENTA, Senal, analizar, combinar


def _ohlc(valores):
    idx = pd.date_range("2025-01-01", periods=len(valores), freq="B")
    c = pd.Series(valores, index=idx, dtype=float)
    return pd.DataFrame({"Open": c, "High": c + 1, "Low": c - 1, "Close": c})


def test_combinar_reglas():
    s = lambda x: Senal(x, "")
    assert combinar(s(COMPRA), s(COMPRA))[0] == COMPRA
    assert combinar(s(VENTA), s(MANTENER))[0] == VENTA
    assert combinar(s(MANTENER), s(COMPRA))[0] == COMPRA
    assert combinar(s(COMPRA), s(VENTA))[0] == MANTENER
    assert combinar(s(MANTENER), s(MANTENER))[0] == MANTENER


def test_analizar_no_pierde_el_sar_en_tendencia_bajista():
    # Con la versión anterior el SAR quedaba en NaN en tendencias bajistas.
    a = analizar(_ohlc(np.linspace(150, 100, 80)), "TEST")
    assert "nan" not in a.sar.nota.lower()
    assert "bajista" in a.sar.nota
    assert {"psar", "k", "d"} <= set(a.datos.columns)


def test_analizar_da_venta_el_dia_de_la_reversa():
    valores = list(np.linspace(100, 150, 60)) + [140.0]
    a = analizar(_ohlc(valores), "TEST")
    assert a.sar.senal == VENTA
