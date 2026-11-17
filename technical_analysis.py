"""Reglas de señal basadas en Parabolic SAR y Oscilador Estocástico."""
from dataclasses import dataclass

import pandas as pd

from indicators import parabolic_sar, stochastic

COMPRA, VENTA, MANTENER = "Compra", "Venta", "Mantener"
SOBREVENTA, SOBRECOMPRA = 20, 80


@dataclass
class Senal:
    senal: str            # Compra / Venta / Mantener
    nota: str             # explicación para el usuario


@dataclass
class Analisis:
    ticker: str
    senal: str
    justificacion: str
    sar: Senal
    estocastico: Senal
    datos: pd.DataFrame   # OHLC + columnas de indicadores (para la gráfica)


def agregar_indicadores(df: pd.DataFrame, k: int = 14, d: int = 3,
                        smooth_k: int = 3) -> pd.DataFrame:
    """Devuelve una copia del DataFrame con PSAR y Estocástico calculados una sola vez."""
    out = df.copy()
    out = out.join(parabolic_sar(out["High"], out["Low"]))
    out = out.join(stochastic(out["High"], out["Low"], out["Close"], k, d, smooth_k))
    return out


def senal_sar(df: pd.DataFrame) -> Senal:
    if len(df) < 2 or df["psar"].iloc[-2:].isna().any():
        return Senal(MANTENER, "Datos insuficientes para Parabolic SAR.")
    precio, psar = df["Close"].iloc[-1], df["psar"].iloc[-1]
    base = f"Precio ({precio:.2f}), PSAR ({psar:.2f}). "
    alcista = df["tendencia"].iloc[-1] == 1
    if df["reversa"].iloc[-1]:
        if alcista:
            return Senal(COMPRA, base + "El precio cruzó por encima del Parabolic SAR (giro alcista).")
        return Senal(VENTA, base + "El precio cruzó por debajo del Parabolic SAR (giro bajista).")
    if alcista:
        return Senal(MANTENER, base + "El precio se mantiene por encima del SAR (tendencia alcista).")
    return Senal(MANTENER, base + "El precio se mantiene por debajo del SAR (tendencia bajista).")


def senal_estocastico(df: pd.DataFrame) -> Senal:
    ultimos = df[["k", "d"]].dropna()
    if len(ultimos) < 2:
        return Senal(MANTENER, "Datos insuficientes para el Oscilador Estocástico.")
    (pk, pd_), (k, d) = ultimos.iloc[-2], ultimos.iloc[-1]
    base = f"%K ({k:.2f}), %D ({d:.2f}). "
    if pk < pd_ and k > d and k < SOBREVENTA:
        return Senal(COMPRA, base + f"%K cruzó por encima de %D en sobreventa (<{SOBREVENTA}).")
    if pk > pd_ and k < d and k > SOBRECOMPRA:
        return Senal(VENTA, base + f"%K cruzó por debajo de %D en sobrecompra (>{SOBRECOMPRA}).")
    if k < SOBREVENTA or d < SOBREVENTA:
        return Senal(MANTENER, base + "Zona de sobreventa; atención a un cruce alcista.")
    if k > SOBRECOMPRA or d > SOBRECOMPRA:
        return Senal(MANTENER, base + "Zona de sobrecompra; atención a un cruce bajista.")
    return Senal(MANTENER, base + "Zona neutral.")


def combinar(sar: Senal, est: Senal) -> tuple[str, str]:
    """Consolida ambas señales en una recomendación."""
    if sar.senal == est.senal != MANTENER:
        return sar.senal, "Ambos indicadores coinciden."
    if MANTENER in (sar.senal, est.senal) and sar.senal != est.senal:
        fuerte, nombre = (sar, "Parabolic SAR") if sar.senal != MANTENER else (est, "Estocástico")
        return fuerte.senal, f"Señal de {nombre}; el otro indicador es neutral."
    if sar.senal != MANTENER and est.senal != MANTENER:
        return MANTENER, "Los indicadores se contradicen; se sugiere esperar confirmación."
    return MANTENER, "Sin señales de entrada o salida en este momento."


def analizar(df_precios: pd.DataFrame, ticker: str) -> Analisis:
    df = agregar_indicadores(df_precios)
    sar, est = senal_sar(df), senal_estocastico(df)
    senal, justificacion = combinar(sar, est)
    return Analisis(ticker, senal, justificacion, sar, est, df)
