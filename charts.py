"""Gráficas del análisis. Devuelve la imagen en memoria (no escribe en disco)."""
import io

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: necesario en servidores y en hilos (macOS)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from technical_analysis import SOBRECOMPRA, SOBREVENTA  # noqa: E402


def grafica_analisis(df: pd.DataFrame, ticker: str, dias: int = 100) -> io.BytesIO:
    """Precio + Parabolic SAR arriba, Oscilador Estocástico abajo."""
    sub = df.tail(dias)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    try:
        ax1.plot(sub.index, sub["Close"], label="Cierre", color="#0B2545", lw=1.6)
        alc = sub["tendencia"] == 1
        ax1.scatter(sub.index[alc], sub["psar"][alc], s=9, color="#1B998B", label="SAR (alcista)")
        ax1.scatter(sub.index[~alc], sub["psar"][~alc], s=9, color="#C0392B", label="SAR (bajista)")
        ax1.set_title(f"{ticker}: precio y Parabolic SAR")
        ax1.legend(loc="upper left")
        ax1.grid(alpha=0.3)

        ax2.plot(sub.index, sub["k"], label="%K", color="#2E86AB")
        ax2.plot(sub.index, sub["d"], label="%D", color="#E8A33D")
        ax2.axhline(SOBRECOMPRA, color="#C0392B", ls="--", alpha=0.6)
        ax2.axhline(SOBREVENTA, color="#1B998B", ls="--", alpha=0.6)
        ax2.set_ylim(0, 100)
        ax2.set_title("Oscilador Estocástico (14, 3, 3)")
        ax2.legend(loc="upper left")
        ax2.grid(alpha=0.3)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        buf.seek(0)
        return buf
    finally:
        plt.close(fig)
