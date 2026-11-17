"""Gráfico de precio + Parabolic SAR + Estocástico.

Usa la API orientada a objetos de matplotlib (Figure) en lugar de pyplot para
poder generarse de forma segura en un hilo secundario.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from technical_analysis import OVERBOUGHT, OVERSOLD, Analysis  # noqa: E402

UP, DOWN, PRICE, K_COLOR, D_COLOR, GRID = "#16a34a", "#dc2626", "#1e3a8a", "#2563eb", "#f59e0b", "#e5e7eb"


def build_chart(analysis: Analysis, days: int = 120) -> bytes:
    """Devuelve el gráfico como PNG en bytes."""
    df = analysis.data.tail(days)

    fig = Figure(figsize=(10, 6.5), dpi=110)
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.2], hspace=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)

    # Precio y SAR (puntos verdes = tendencia alcista, rojos = bajista)
    ax1.plot(df.index, df["Close"], color=PRICE, lw=1.6, label="Cierre")
    up = df["PSAR_TREND"] == 1
    ax1.scatter(df.index[up], df["PSAR"][up], s=9, color=UP, label="SAR alcista", zorder=3)
    ax1.scatter(df.index[~up], df["PSAR"][~up], s=9, color=DOWN, label="SAR bajista", zorder=3)
    ax1.annotate(f"{analysis.last_close:,.2f}", xy=(df.index[-1], df["Close"].iloc[-1]),
                 xytext=(6, 0), textcoords="offset points", va="center", fontsize=9,
                 color="white", bbox=dict(boxstyle="round,pad=0.25", fc=PRICE, ec="none"))
    ax1.set_title(f"{analysis.ticker} · Señal: {analysis.signal.upper()}"
                  + (f" ({analysis.strength.lower()})" if analysis.strength else ""),
                  loc="left", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Precio")
    ax1.legend(loc="upper left", fontsize=8, frameon=False, ncol=3)

    # Estocástico
    ax2.plot(df.index, df["STOCH_K"], color=K_COLOR, lw=1.2, label="%K")
    ax2.plot(df.index, df["STOCH_D"], color=D_COLOR, lw=1.2, label="%D")
    ax2.axhspan(OVERBOUGHT, 100, color=DOWN, alpha=0.07)
    ax2.axhspan(0, OVERSOLD, color=UP, alpha=0.07)
    ax2.axhline(OVERBOUGHT, color=DOWN, ls="--", lw=0.8)
    ax2.axhline(OVERSOLD, color=UP, ls="--", lw=0.8)
    ax2.set_ylim(0, 100)
    ax2.set_yticks([0, OVERSOLD, 50, OVERBOUGHT, 100])
    ax2.set_ylabel("Estocástico")
    ax2.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)

    for ax in (ax1, ax2):
        ax.grid(True, color=GRID, lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    ax1.tick_params(labelbottom=False)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    return buf.getvalue()
