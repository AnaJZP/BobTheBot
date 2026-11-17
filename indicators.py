"""Indicadores técnicos implementados con pandas/numpy (sin dependencias externas).

Se implementan aquí para que las fórmulas sean transparentes y para no depender
de pandas_ta, cuya versión 0.3.14b0 ya no está disponible en PyPI.
"""
import numpy as np
import pandas as pd


def parabolic_sar(high: pd.Series, low: pd.Series, af0: float = 0.02,
                  af_step: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
    """Parabolic SAR de Wilder.

    Devuelve un DataFrame con:
      - psar:      valor del SAR (una sola serie, sin huecos)
      - tendencia: 1 alcista (SAR debajo del precio), -1 bajista (SAR arriba)
      - reversa:   True en el día en que cambia la tendencia
    """
    h = high.to_numpy(dtype=float)
    lo = low.to_numpy(dtype=float)
    n = len(h)
    if n < 2:
        raise ValueError("Se requieren al menos 2 observaciones para el Parabolic SAR.")

    sar = np.empty(n)
    trend = np.empty(n, dtype=int)
    reversal = np.zeros(n, dtype=bool)

    # Tendencia inicial según el movimiento direccional de las dos primeras barras
    alcista = (h[1] - h[0]) >= (lo[0] - lo[1])
    sar[0] = lo[0] if alcista else h[0]
    ep = h[0] if alcista else lo[0]          # punto extremo
    af = af0
    trend[0] = 1 if alcista else -1

    for i in range(1, n):
        s = sar[i - 1] + af * (ep - sar[i - 1])
        if alcista:
            s = min(s, lo[i - 1], lo[i - 2] if i >= 2 else lo[i - 1])
            if lo[i] < s:                      # el precio perfora el SAR: reversa
                alcista, s, ep, af = False, ep, lo[i], af0
                reversal[i] = True
            elif h[i] > ep:
                ep, af = h[i], min(af + af_step, af_max)
        else:
            s = max(s, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > s:
                alcista, s, ep, af = True, ep, h[i], af0
                reversal[i] = True
            elif lo[i] < ep:
                ep, af = lo[i], min(af + af_step, af_max)
        sar[i] = s
        trend[i] = 1 if alcista else -1

    return pd.DataFrame({"psar": sar, "tendencia": trend, "reversa": reversal},
                        index=high.index)


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14,
               d: int = 3, smooth_k: int = 3) -> pd.DataFrame:
    """Oscilador Estocástico lento (%K suavizado y %D), escala 0-100."""
    minimo = low.rolling(k).min()
    maximo = high.rolling(k).max()
    rango = (maximo - minimo).replace(0, np.nan)
    k_raw = 100 * (close - minimo) / rango
    k_line = k_raw.rolling(smooth_k).mean()
    d_line = k_line.rolling(d).mean()
    return pd.DataFrame({"k": k_line, "d": d_line}, index=close.index)
