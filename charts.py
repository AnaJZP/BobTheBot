"""Gráfico de velas + Parabolic SAR + Estocástico.

Usa la API orientada a objetos de matplotlib (Figure) en lugar de pyplot para
poder generarse de forma segura en un hilo secundario.

Las velas se dibujan sobre posiciones enteras (0, 1, 2…) en lugar de fechas, así no
quedan huecos en noches, fines de semana ni días feriados.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402

from technical_analysis import OVERBOUGHT, OVERSOLD, Analysis  # noqa: E402

UP, DOWN, PRICE, K_COLOR, D_COLOR, GRID = "#16a34a", "#dc2626", "#1e3a8a", "#2563eb", "#f59e0b", "#e5e7eb"
TF_LABEL = {"1h": "velas de 1 hora", "4h": "velas de 4 horas", "1d": "velas diarias"}
DATE_FMT = {"1h": "%d %b %H:%M", "4h": "%d %b %H:%M", "1d": "%d %b %y"}


def _candles(ax, df, width=0.62):
    x = np.arange(len(df))
    o, h, l, c = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    up = c >= o
    colors = np.where(up, UP, DOWN)

    ax.add_collection(LineCollection([[(xi, lo), (xi, hi)] for xi, lo, hi in zip(x, l, h)],
                                     colors=colors, linewidths=0.8, zorder=2))
    body_lo, body_hi = np.minimum(o, c), np.maximum(o, c)
    # cuerpo mínimo visible cuando apertura ≈ cierre (doji)
    min_body = (np.nanmax(h) - np.nanmin(l)) * 0.0015
    body_hi = np.maximum(body_hi, body_lo + min_body)
    w = width / 2
    ax.add_collection(PolyCollection(
        [[(xi - w, lo), (xi - w, hi), (xi + w, hi), (xi + w, lo)] for xi, lo, hi in zip(x, body_lo, body_hi)],
        facecolors=colors, edgecolors=colors, linewidths=0.5, zorder=3))
    ax.set_xlim(-1, len(df) + 2)
    pad = (np.nanmax(h) - np.nanmin(l)) * 0.05
    ax.set_ylim(np.nanmin(np.r_[l, df["PSAR"].min()]) - pad, np.nanmax(np.r_[h, df["PSAR"].max()]) + pad)


def build_chart(analysis: Analysis, bars: int = 120) -> bytes:
    """Devuelve el gráfico como PNG en bytes."""
    df = analysis.data.tail(bars)
    x = np.arange(len(df))

    fig = Figure(figsize=(10, 6.5), dpi=110)
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.2], hspace=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)

    # Velas y SAR (puntos verdes = tendencia alcista, rojos = bajista)
    _candles(ax1, df)
    up = (df["PSAR_TREND"] == 1).to_numpy()
    sar = df["PSAR"].to_numpy()
    ax1.scatter(x[up], sar[up], s=7, color=UP, label="SAR alcista", zorder=4)
    ax1.scatter(x[~up], sar[~up], s=7, color=DOWN, label="SAR bajista", zorder=4)
    last = df["Close"].iloc[-1]
    ax1.axhline(last, color=PRICE, lw=0.6, ls=":", zorder=1)
    ax1.annotate(f"{last:,.2f}", xy=(len(df) - 1, last), xytext=(8, 0), textcoords="offset points",
                 va="center", fontsize=9, color="white",
                 bbox=dict(boxstyle="round,pad=0.25", fc=PRICE, ec="none"), annotation_clip=False)
    title = f"{analysis.ticker} · Señal: {analysis.signal.upper()}"
    if analysis.strength:
        title += f" ({analysis.strength.lower()})"
    ax1.set_title(title, loc="left", fontsize=13, fontweight="bold")
    ax1.set_title(TF_LABEL.get(analysis.timeframe, ""), loc="right", fontsize=9, color="#6b7280")
    ax1.set_ylabel("Precio")
    ax1.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)

    # Estocástico
    ax2.plot(x, df["STOCH_K"], color=K_COLOR, lw=1.2, label="%K")
    ax2.plot(x, df["STOCH_D"], color=D_COLOR, lw=1.2, label="%D")
    ax2.axhspan(OVERBOUGHT, 100, color=DOWN, alpha=0.07)
    ax2.axhspan(0, OVERSOLD, color=UP, alpha=0.07)
    ax2.axhline(OVERBOUGHT, color=DOWN, ls="--", lw=0.8)
    ax2.axhline(OVERSOLD, color=UP, ls="--", lw=0.8)
    ax2.set_ylim(0, 100)
    ax2.set_yticks([0, OVERSOLD, 50, OVERBOUGHT, 100])
    ax2.set_ylabel("Estocástico")
    ax2.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)

    # Eje X: posiciones enteras etiquetadas con la fecha de cada vela
    fmt = DATE_FMT.get(analysis.timeframe, "%d %b %y")
    labels = [ts.strftime(fmt) for ts in df.index]
    ax2.xaxis.set_major_locator(MaxNLocator(nbins=7, integer=True))
    ax2.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: labels[int(v)] if 0 <= int(v) < len(labels) else ""))

    for ax in (ax1, ax2):
        ax.grid(True, color=GRID, lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    ax1.tick_params(labelbottom=False)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    return buf.getvalue()
