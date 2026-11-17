"""Indicadores técnicos (Parabolic SAR y Oscilador Estocástico) y señal combinada.

Los indicadores se calculan con pandas/numpy puros (sin pandas_ta), una sola vez
por consulta, y el mismo DataFrame se reutiliza para el gráfico.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

COMPRA, VENTA, MANTENER = "Compra", "Venta", "Mantener"

PSAR_STEP, PSAR_MAX = 0.02, 0.2
STOCH_K, STOCH_D, STOCH_SMOOTH = 14, 3, 3
OVERSOLD, OVERBOUGHT = 20, 80


# --------------------------------------------------------------------------- #
# Cálculo de indicadores
# --------------------------------------------------------------------------- #
def parabolic_sar(high: pd.Series, low: pd.Series, step: float = PSAR_STEP,
                  max_af: float = PSAR_MAX) -> tuple[pd.Series, pd.Series]:
    """Parabolic SAR de Wilder.

    Devuelve (sar, tendencia) donde tendencia es +1 (alcista: SAR debajo del
    precio) o -1 (bajista: SAR encima del precio).
    """
    h, l = high.to_numpy(float), low.to_numpy(float)
    n = len(h)
    sar = np.full(n, np.nan)
    trend = np.zeros(n, dtype=int)
    if n < 2:
        return pd.Series(sar, index=high.index), pd.Series(trend, index=high.index)

    up = h[1] >= h[0]
    ep = h[1] if up else l[1]
    af = step
    sar[1] = l[0] if up else h[0]
    trend[1] = 1 if up else -1

    for i in range(2, n):
        s = sar[i - 1] + af * (ep - sar[i - 1])
        if up:
            s = min(s, l[i - 1], l[i - 2])
            if l[i] < s:                      # reversión a bajista
                up, s, ep, af = False, ep, l[i], step
            elif h[i] > ep:
                ep, af = h[i], min(af + step, max_af)
        else:
            s = max(s, h[i - 1], h[i - 2])
            if h[i] > s:                      # reversión a alcista
                up, s, ep, af = True, ep, h[i], step
            elif l[i] < ep:
                ep, af = l[i], min(af + step, max_af)
        sar[i] = s
        trend[i] = 1 if up else -1

    return pd.Series(sar, index=high.index), pd.Series(trend, index=high.index)


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k: int = STOCH_K,
               d: int = STOCH_D, smooth_k: int = STOCH_SMOOTH) -> tuple[pd.Series, pd.Series]:
    """Oscilador Estocástico lento (k, d, smooth_k). Devuelve (%K, %D)."""
    lowest = low.rolling(k).min()
    highest = high.rolling(k).max()
    rng = (highest - lowest).replace(0, np.nan)
    raw_k = 100 * (close - lowest) / rng
    pct_k = raw_k.rolling(smooth_k).mean()
    pct_d = pct_k.rolling(d).mean()
    return pct_k, pct_d


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia del DataFrame con columnas PSAR, PSAR_TREND, STOCH_K y STOCH_D."""
    out = df.copy()
    out["PSAR"], out["PSAR_TREND"] = parabolic_sar(out["High"], out["Low"])
    out["STOCH_K"], out["STOCH_D"] = stochastic(out["High"], out["Low"], out["Close"])
    return out


# --------------------------------------------------------------------------- #
# Interpretación
# --------------------------------------------------------------------------- #
@dataclass
class IndicatorResult:
    signal: str          # Compra / Venta / Mantener
    summary: str         # resumen corto (ej. "Tendencia alcista")
    note: str            # explicación en lenguaje natural


@dataclass
class Analysis:
    ticker: str
    signal: str
    strength: str        # Fuerte / Moderada / "" (si es Mantener)
    justification: str
    psar: IndicatorResult
    stoch: IndicatorResult
    last_close: float
    last_date: pd.Timestamp
    data: pd.DataFrame   # DataFrame con indicadores (para graficar)
    timeframe: str = "1d"


def analyze_parabolic_sar(df: pd.DataFrame) -> IndicatorResult:
    valid = df.dropna(subset=["PSAR"])
    if len(valid) < 2:
        return IndicatorResult(MANTENER, "Sin datos", "Datos insuficientes para el Parabolic SAR.")

    last, prev = valid.iloc[-1], valid.iloc[-2]
    close, sar = last["Close"], last["PSAR"]
    dist = (close - sar) / close * 100

    if last["PSAR_TREND"] == 1 and prev["PSAR_TREND"] == -1:
        return IndicatorResult(COMPRA, "Giro alcista",
                               f"El precio ({close:.2f}) cruzó por encima del SAR ({sar:.2f}): posible inicio de tendencia alcista.")
    if last["PSAR_TREND"] == -1 and prev["PSAR_TREND"] == 1:
        return IndicatorResult(VENTA, "Giro bajista",
                               f"El precio ({close:.2f}) cruzó por debajo del SAR ({sar:.2f}): posible inicio de tendencia bajista.")
    if last["PSAR_TREND"] == 1:
        return IndicatorResult(MANTENER, "Tendencia alcista",
                               f"El SAR ({sar:.2f}) sigue debajo del precio ({close:.2f}, {dist:+.1f}%). Sin cruce nuevo.")
    return IndicatorResult(MANTENER, "Tendencia bajista",
                           f"El SAR ({sar:.2f}) sigue encima del precio ({close:.2f}, {dist:+.1f}%). Sin cruce nuevo.")


def analyze_stochastic_oscillator(df: pd.DataFrame) -> IndicatorResult:
    valid = df.dropna(subset=["STOCH_K", "STOCH_D"])
    if len(valid) < 2:
        return IndicatorResult(MANTENER, "Sin datos", "Datos insuficientes para el Oscilador Estocástico.")

    k, d = valid["STOCH_K"].iloc[-1], valid["STOCH_D"].iloc[-1]
    pk, pd_ = valid["STOCH_K"].iloc[-2], valid["STOCH_D"].iloc[-2]
    summary = f"%K {k:.1f} · %D {d:.1f}"

    crossed_up = pk <= pd_ and k > d
    crossed_down = pk >= pd_ and k < d

    if crossed_up and min(pk, k) < OVERSOLD:
        return IndicatorResult(COMPRA, summary, f"%K cruzó por encima de %D en zona de sobreventa (<{OVERSOLD}).")
    if crossed_down and max(pk, k) > OVERBOUGHT:
        return IndicatorResult(VENTA, summary, f"%K cruzó por debajo de %D en zona de sobrecompra (>{OVERBOUGHT}).")
    if k < OVERSOLD:
        return IndicatorResult(MANTENER, summary, f"En sobreventa (<{OVERSOLD}). Atento a un cruce alcista.")
    if k > OVERBOUGHT:
        return IndicatorResult(MANTENER, summary, f"En sobrecompra (>{OVERBOUGHT}). Atento a un cruce bajista.")
    return IndicatorResult(MANTENER, summary, "Zona neutral, sin cruces relevantes.")


def analyze(df: pd.DataFrame, ticker: str, timeframe: str = "1d") -> Analysis:
    """Calcula indicadores y genera la recomendación combinada."""
    data = compute_indicators(df)
    psar = analyze_parabolic_sar(data)
    stoch = analyze_stochastic_oscillator(data)

    signals = {psar.signal, stoch.signal} - {MANTENER}
    if len(signals) == 2:
        signal, strength = MANTENER, ""
        justification = "Los indicadores se contradicen (uno sugiere compra y otro venta). Mejor esperar confirmación."
    elif psar.signal == stoch.signal != MANTENER:
        signal, strength = psar.signal, "Fuerte"
        justification = "Ambos indicadores coinciden en la misma señal."
    elif signals:
        signal, strength = signals.pop(), "Moderada"
        name, other = ("Parabolic SAR", "Estocástico") if psar.signal != MANTENER else ("Estocástico", "Parabolic SAR")
        justification = f"Señal del {name}; el {other} no la contradice."
        trend = data["PSAR_TREND"].iloc[-1]
        if stoch.signal != MANTENER and (trend == 1) != (signal == COMPRA):
            strength = "Débil"
            justification = "Señal del Estocástico, pero va en contra de la tendencia del Parabolic SAR."
    else:
        signal, strength = MANTENER, ""
        justification = f"Sin cruces nuevos. SAR: {psar.summary.lower()}. Estocástico: {stoch.note}"

    return Analysis(
        ticker=ticker, signal=signal, strength=strength, justification=justification,
        psar=psar, stoch=stoch, last_close=float(data["Close"].iloc[-1]),
        last_date=data.index[-1], data=data, timeframe=timeframe,
    )


if __name__ == "__main__":
    from data_provider import get_market_data

    md = get_market_data("MSFT")
    if md:
        a = analyze(md.history, "MSFT", md.timeframe)
        print(f"{a.ticker}: {a.signal} {a.strength}\n{a.justification}\n"
              f"PSAR: {a.psar.signal} – {a.psar.note}\nStoch: {a.stoch.signal} – {a.stoch.note}")
