import numpy as np
import pandas as pd

from indicators import parabolic_sar, stochastic


def _serie(valores):
    idx = pd.date_range("2025-01-01", periods=len(valores), freq="B")
    close = pd.Series(valores, index=idx, dtype=float)
    return close + 1, close - 1, close          # high, low, close


def test_psar_en_tendencia_alcista_queda_debajo_del_minimo():
    high, low, _ = _serie(np.linspace(100, 150, 60))
    r = parabolic_sar(high, low)
    assert (r["tendencia"].iloc[1:] == 1).all()
    assert (r["psar"].iloc[2:] <= low.iloc[2:]).all()


def test_psar_detecta_reversa_tras_una_caida():
    valores = list(np.linspace(100, 150, 40)) + list(np.linspace(148, 110, 20))
    high, low, _ = _serie(valores)
    r = parabolic_sar(high, low)
    assert r["reversa"].iloc[40:].any()
    assert r["tendencia"].iloc[-1] == -1
    assert r["psar"].notna().all()           # una sola serie, sin huecos


def test_estocastico_en_rango_y_extremos():
    high, low, close = _serie(np.linspace(100, 150, 60))
    st = stochastic(high, low, close).dropna()
    assert st["k"].between(0, 100).all() and st["d"].between(0, 100).all()
    assert st["k"].iloc[-1] > 80             # cierre cerca del máximo -> sobrecompra
