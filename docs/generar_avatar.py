"""Genera el avatar de Bob the Bot (docs/assets/bob_avatar.png, 640x640).

    python docs/generar_avatar.py

Telegram recorta la foto de perfil en círculo, por eso el dibujo queda centrado.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402

OUT = Path(__file__).resolve().parent / "assets" / "bob_avatar.png"

NAVY, BLUE, LIGHT, WHITE = "#1e3a8a", "#2563eb", "#dbeafe", "#ffffff"
GREEN, RED, SCREEN = "#22c55e", "#ef4444", "#0f172a"


def build(path: Path = OUT) -> Path:
    fig = Figure(figsize=(6.4, 6.4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor(NAVY)

    # Halo de fondo
    ax.add_patch(Circle((50, 50), 46, color=BLUE, alpha=0.35, lw=0))

    # Antena
    ax.plot([50, 50], [74, 84], color=LIGHT, lw=6, solid_capstyle="round")
    ax.add_patch(Circle((50, 86), 4.2, color=GREEN))

    # Orejas
    for x in (19, 75):
        ax.add_patch(FancyBboxPatch((x, 43), 6, 14, boxstyle="round,pad=0,rounding_size=2.5",
                                    fc=LIGHT, ec="none"))

    # Cabeza
    ax.add_patch(FancyBboxPatch((24, 26), 52, 48, boxstyle="round,pad=0,rounding_size=10",
                                fc=WHITE, ec="none"))

    # Pantalla (cara)
    ax.add_patch(FancyBboxPatch((30, 33), 40, 34, boxstyle="round,pad=0,rounding_size=7",
                                fc=SCREEN, ec="none"))

    # Ojos
    for x in (41, 59):
        ax.add_patch(Circle((x, 56), 4.3, color=LIGHT))
        ax.add_patch(Circle((x + 1, 57), 1.6, color=SCREEN))

    # "Sonrisa" en forma de gráfico al alza con velas
    xs = [35, 41, 46, 51, 56, 61, 65]
    ys = [39, 42, 40, 44, 43, 46, 48.5]
    ax.plot(xs, ys, color=GREEN, lw=3.2, solid_joinstyle="round", solid_capstyle="round")
    ax.add_patch(Polygon([[65, 48.5], [61.3, 47.6], [63.6, 44.8]], closed=True, color=GREEN))
    for x, lo, hi, up in ((38, 37.5, 41.5, False), (48.5, 38, 42.5, True), (58.5, 39, 44, True)):
        ax.plot([x, x], [lo - 1.2, hi + 1.2], color=GREEN if up else RED, lw=0.9)
        ax.add_patch(FancyBboxPatch((x - 1.1, lo), 2.2, hi - lo, boxstyle="square,pad=0",
                                    fc=GREEN if up else RED, ec="none"))

    # Cuello / base
    ax.add_patch(FancyBboxPatch((40, 17), 20, 8, boxstyle="round,pad=0,rounding_size=3",
                                fc=LIGHT, ec="none"))

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=NAVY)
    return path


if __name__ == "__main__":
    print(f"✓ {build()}")
