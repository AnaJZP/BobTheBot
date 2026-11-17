"""Genera el manual en PDF de Bob the Bot (Manual_Bob_the_Bot.pdf).

    pip install reportlab
    python docs/generar_pdfs.py [--bot-username @MiBot] [--out carpeta]

El manual tiene tres partes: I. Puesta en marcha (desde @BotFather),
II. Uso del bot y III. Funcionamiento interno. Si hay conexión a internet,
incluye un gráfico real generado por el propio bot.
"""
from __future__ import annotations

import argparse
import io
import sys
from datetime import date
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------------- #
# Estilo
# ----------------------------------------------------------------------------- #
NAVY = colors.HexColor("#1e3a8a")
BLUE = colors.HexColor("#2563eb")
LIGHT = colors.HexColor("#eff6ff")
GREY = colors.HexColor("#6b7280")
LINE = colors.HexColor("#d1d5db")
GREEN = colors.HexColor("#16a34a")
RED = colors.HexColor("#dc2626")
AMBER = colors.HexColor("#d97706")
CODE_BG = colors.HexColor("#f3f4f6")

INSTITUTION = "SEPI ESE IPN"
COURSE = "Análisis Bursátil y Métodos Algorítmicos Avanzados"
AUTHOR = "Ana Lorena Jiménez Preciado"

ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=24,
                            leading=29, textColor=NAVY, alignment=0, spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", parent=ss["Normal"], fontSize=12, leading=16,
                               textColor=GREY, spaceAfter=14),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15,
                         leading=19, textColor=NAVY, spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5,
                         leading=15, textColor=colors.black, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=10,
                           leading=14.5, spaceAfter=6),
    "small": ParagraphStyle("small", parent=ss["Normal"], fontSize=8.5, leading=11, textColor=GREY),
    "cell": ParagraphStyle("cell", parent=ss["Normal"], fontSize=9, leading=12),
    "cellb": ParagraphStyle("cellb", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9,
                            leading=12, textColor=colors.white),
    "code": ParagraphStyle("code", parent=ss["Code"], fontName="Courier", fontSize=8.8, leading=12,
                           backColor=CODE_BG, borderPadding=(6, 8, 6, 8), leftIndent=8, rightIndent=8,
                           spaceBefore=4, spaceAfter=10),
    "callout": ParagraphStyle("callout", parent=ss["Normal"], fontSize=9.5, leading=13.5,
                              backColor=LIGHT, borderColor=BLUE, borderWidth=0, borderPadding=8,
                              leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=12),
    "caption": ParagraphStyle("caption", parent=ss["Normal"], fontSize=8.5, leading=11,
                              textColor=GREY, alignment=TA_CENTER, spaceAfter=10),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def code(text):
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(esc.replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;"), S["code"])


def bullets(items, style="body"):
    return ListFlowable([ListItem(P(i, style), leftIndent=12, value="•") for i in items],
                        bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9)


def table(rows, widths, header=True, zebra=True):
    data = [[c if not isinstance(c, str) else P(c, "cellb" if header and r == 0 else "cell")
             for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for r in range(1 if header else 0, len(rows)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f9fafb")))
    t.setStyle(TableStyle(style))
    return t


def cover(title, subtitle):
    return [
        P(f"<font color='#6b7280'>{INSTITUTION}  ·  {COURSE.upper()}</font>", "small"),
        Spacer(1, 2),
        P(f"<font color='#6b7280'>{AUTHOR}</font>", "small"),
        Spacer(1, 18),
        P(title, "title"),
        P(subtitle, "subtitle"),
        Table([[""]], colWidths=[17 * cm], rowHeights=[2],
              style=[("BACKGROUND", (0, 0), (-1, -1), BLUE)]),
        Spacer(1, 10),
    ]


def make_page_decor(doc_title):
    def decor(canvas, doc):
        canvas.saveState()
        w, h = letter
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawString(2.2 * cm, 1.3 * cm, f"Bob the Bot · {doc_title}")
        canvas.drawRightString(w - 2.2 * cm, 1.3 * cm, f"Página {doc.page}")
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(2.2 * cm, 1.7 * cm, w - 2.2 * cm, 1.7 * cm)
        canvas.restoreState()
    return decor


def build(path, story, doc_title):
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2 * cm, bottomMargin=2.3 * cm, title=f"Bob the Bot – {doc_title}",
                            author=AUTHOR, subject=COURSE)
    decor = make_page_decor(doc_title)
    doc.build(story, onFirstPage=decor, onLaterPages=decor)
    print(f"✓ {path.name}")


# ----------------------------------------------------------------------------- #
# Diagramas
# ----------------------------------------------------------------------------- #
def _box(d, x, y, w, h, title, sub=None, fill=LIGHT, stroke=BLUE, title_color=NAVY):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor=stroke, strokeWidth=0.9))
    ty = y + h / 2 + (3 if sub else -3.5)
    d.add(String(x + w / 2, ty, title, fontName="Helvetica-Bold", fontSize=9,
                 fillColor=title_color, textAnchor="middle"))
    if sub:
        d.add(String(x + w / 2, ty - 11, sub, fontName="Helvetica", fontSize=7.5,
                     fillColor=GREY, textAnchor="middle"))


def _arrow(d, x1, y1, x2, y2, color=GREY):
    import math
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1))
    ang = math.atan2(y2 - y1, x2 - x1)
    s = 5
    p1 = (x2 - s * math.cos(ang - 0.4), y2 - s * math.sin(ang - 0.4))
    p2 = (x2 - s * math.cos(ang + 0.4), y2 - s * math.sin(ang + 0.4))
    d.add(Polygon([x2, y2, *p1, *p2], fillColor=color, strokeColor=color, strokeWidth=0.5))


def architecture_diagram():
    W, H = 17 * cm, 7.4 * cm
    d = Drawing(W, H)
    bh = 1.1 * cm
    sw, cw = 4.6 * cm, 4.2 * cm                 # ancho de cajas laterales / centrales
    cx = W / 2 - cw / 2
    side_h = H - 0.1 * cm                       # alto útil para las columnas laterales
    bot_y = (H - bh) / 2 - 0.5 * cm

    _box(d, cx, H - bh - 2, cw, bh, "main.py", "punto de entrada", fill=colors.white)
    _box(d, cx, bot_y, cw, bh, "bot_logic.py", "Telegram + orquestación",
         fill=NAVY, stroke=NAVY, title_color=colors.white)
    _arrow(d, W / 2, H - bh - 2, W / 2, bot_y + bh + 1)

    left = [("config.py", ".env / token"), ("ticker_parser.py", "texto → ticker + ventana"),
            ("catalog.py", "mercados → sectores → activos"), ("query_logger.py", "historial CSV")]
    right = [("data_provider.py", "yfinance 1h · 4h · 1d + caché"),
             ("technical_analysis.py", "SAR + Estocástico → señal"), ("charts.py", "gráfico de velas PNG")]
    mid_y = bot_y + bh / 2

    def column(items, x, arrow_from, arrow_to_x):
        n = len(items)
        step = (side_h - bh) / (n - 1)
        for i, (name, sub) in enumerate(items):
            y = side_h - bh - i * step
            _box(d, x, y, sw, bh, name, sub)
            _arrow(d, arrow_from, mid_y, arrow_to_x, y + bh / 2)

    column(left, 0, cx, sw + 1)
    column(right, W - sw, cx + cw, W - sw - 1)
    return d


def flow_diagram():
    steps = [
        ("1. Usuario", "mensaje, /analizar, menú de mercados o botón", colors.white),
        ("2. Handler", "handle_message · analizar_command · button_callback", LIGHT),
        ("3. ticker_parser", "extract_ticker() y extract_timeframe() (1h · 4h · 1d)", LIGHT),
        ("4. Hilo secundario", "asyncio.to_thread(_run_pipeline)", colors.HexColor("#fef3c7")),
        ("   4a. data_provider", "get_market_data(ticker, ventana): velas + precio (caché 5 min)", colors.white),
        ("   4b. technical_analysis", "analyze(): indicadores una sola vez → señal", colors.white),
        ("   4c. charts", "build_chart(): velas + SAR + Estocástico (PNG)", colors.white),
        ("5. Respuesta", "foto + análisis + botones 1h/4h/1d, Actualizar y Mercados", LIGHT),
        ("6. query_logger", "log_query() → consultas_bot.csv", LIGHT),
    ]
    W = 17 * cm
    bh, gap = 0.95 * cm, 0.32 * cm
    H = len(steps) * (bh + gap)
    d = Drawing(W, H)
    for i, (title, sub, fill) in enumerate(steps):
        y = H - (i + 1) * (bh + gap) + gap
        indent = 1.4 * cm if title.startswith("   ") else 0
        x, w = indent, W - indent
        d.add(Rect(x, y, w, bh, rx=4, ry=4, fillColor=fill, strokeColor=BLUE, strokeWidth=0.7))
        d.add(String(x + 8, y + bh / 2 - 3.5, title.strip(), fontName="Helvetica-Bold", fontSize=9,
                     fillColor=NAVY))
        d.add(String(x + 4.6 * cm, y + bh / 2 - 3.5, sub, fontName="Helvetica", fontSize=8.5,
                     fillColor=colors.black))
        if i < len(steps) - 1:
            ax = 0.7 * cm if not steps[i + 1][0].startswith("   ") else 2.1 * cm
            _arrow(d, ax, y, ax, y - gap + 0.5)
    return d


# ----------------------------------------------------------------------------- #
# Gráfico de ejemplo (real, si hay red)
# ----------------------------------------------------------------------------- #
ASSETS = Path(__file__).resolve().parent / "assets"


def sample_output(ticker="AAPL"):
    """Devuelve (png, ticker, texto_html) de una respuesta real del bot.

    Con conexión genera un ejemplo nuevo y lo guarda en docs/assets/; sin conexión
    reutiliza el último ejemplo guardado.
    """
    png_path, txt_path = ASSETS / "ejemplo_respuesta.png", ASSETS / "ejemplo_respuesta.txt"
    try:
        from bot_logic import format_analysis
        from charts import build_chart
        from data_provider import get_market_data
        from technical_analysis import analyze

        md = get_market_data(ticker)
        if md is not None:
            a = analyze(md.history, ticker)
            png, txt = build_chart(a), format_analysis(a, md.price, md.currency)
            ASSETS.mkdir(exist_ok=True)
            png_path.write_bytes(png)
            txt_path.write_text(f"{ticker}\n{txt}", encoding="utf-8")
            return png, ticker, txt
    except Exception as e:  # dependencias del bot no instaladas, etc.
        print(f"  (no se pudo generar un ejemplo nuevo: {e})")

    if png_path.exists() and txt_path.exists():
        print("  (sin conexión: se usa el último ejemplo guardado en docs/assets/)")
        saved_ticker, _, txt = txt_path.read_text(encoding="utf-8").partition("\n")
        return png_path.read_bytes(), saved_ticker, txt
    print("  (sin gráfico de ejemplo)")
    return None, None, None


def telegram_text_to_rl(html_text):
    """Convierte el HTML de Telegram a marcado de ReportLab (quitando emojis)."""
    import re
    t = re.sub(r"[\U0001F000-\U0001FFFF⌀-⏿☀-➿️]", "", html_text)
    t = t.replace("<code>", "<font name='Courier'>").replace("</code>", "</font>")
    return t.strip().replace("\n", "<br/>")



def mono(t):
    return f"<font face='Courier'>{t}</font>"


def numbered(items):
    return ListFlowable([ListItem(P(t), leftIndent=14) for t in items], bulletType="1", leftIndent=16)


def part_header(num, title, desc):
    return [PageBreak(),
            P(f"<font color='#2563eb'>PARTE {num}</font>", "small"),
            P(title, "part"),
            P(desc, "subtitle"),
            Table([[""]], colWidths=[17 * cm], rowHeights=[1.5],
                  style=[("BACKGROUND", (0, 0), (-1, -1), LINE)]),
            Spacer(1, 4)]


S["part"] = ParagraphStyle("part", parent=S["title"], fontSize=20, leading=24, spaceAfter=2)


# ----------------------------------------------------------------------------- #
# Parte I — Puesta en marcha (desde @BotFather)
# ----------------------------------------------------------------------------- #
def part_setup(bot_username):
    st = [P("1. Requisitos", "h1"),
          bullets([
              "Python 3.10 o superior (" + mono("python3 --version") + ").",
              "Una cuenta de Telegram (app en el celular o Telegram Desktop).",
              "Conexión a internet: el bot habla con los servidores de Telegram y descarga precios de "
              "Yahoo! Finance.",
          ])]

    st += [P("2. Crear el bot con @BotFather", "h1"),
           P("@BotFather es el bot oficial de Telegram para crear y administrar bots. Ahí obtienes el "
             "<b>token</b>, la «llave» con la que el programa se conecta a Telegram."),
           numbered([
               "En Telegram busca <b>@BotFather</b> (tiene la palomita azul de verificado) y toca "
               "<b>Iniciar</b>.",
               "Envía " + mono("/newbot") + ".",
               "Escribe el <b>nombre visible</b> del bot, por ejemplo <i>Bob Análisis Bursátil</i>.",
               "Escribe el <b>usuario</b>: debe ser único y terminar en <i>bot</i>, por ejemplo "
               f"<b>{bot_username.lstrip('@')}</b>.",
               "BotFather responde con un mensaje que incluye el token, con un formato como "
               + mono("123456789:AAH...") + ". Cópialo.",
           ]),
           P("<b>El token es una contraseña.</b> Quien lo tenga puede controlar el bot. No lo subas a "
             "GitHub ni lo pegues en el código. Si se filtra, en @BotFather usa " + mono("/revoke") +
             " para invalidarlo y obtener uno nuevo.", "callout"),
           P("Personalización opcional en @BotFather", "h2"),
           table([
               ["Comando", "Para qué"],
               ["/setdescription", "Texto que ve el usuario antes de tocar Iniciar."],
               ["/setabouttext", "Descripción corta del perfil del bot."],
               ["/setuserpic", "Foto de perfil del bot."],
           ], [4.2 * cm, 12.8 * cm]),
           P("No hace falta configurar los comandos con " + mono("/setcommands") + ": Bob registra "
             "automáticamente /mercados, /analizar, /ayuda y /start al arrancar.", "small")]

    st += [P("3. Descargar el proyecto e instalar dependencias", "h1"),
           code("git clone https://github.com/AnaJZP/BobTheBot.git\n"
                "cd BobTheBot\n"
                "python3 -m venv venv\n"
                "source venv/bin/activate        # Windows: venv\\Scripts\\activate\n"
                "pip install -r requirements.txt"),
           P("El entorno virtual (" + mono("venv") + ") mantiene las librerías del proyecto separadas "
             "del resto del sistema. Actívalo cada vez que abras una terminal nueva.")]

    st += [P("4. Configurar el token", "h1"),
           P("Crea un archivo llamado " + mono(".env") + " en la carpeta del proyecto (junto a "
             + mono("main.py") + ") con esta línea:"),
           code("TELEGRAM_BOT_TOKEN=123456789:AAH...tu-token..."),
           bullets([
               "Una sola línea, sin comillas y sin espacios alrededor del " + mono("=") + ".",
               "Guarda el archivo antes de ejecutar el bot.",
               mono(".env") + " está en " + mono(".gitignore") + ": nunca se sube al repositorio.",
           ])]

    st += [P("5. Ejecutar y verificar", "h1"),
           code("python main.py"),
           P("Si todo está bien verás en la terminal:"),
           code("... INFO bot_logic: Bot iniciado. Presiona Ctrl+C para detener."),
           P(f"Abre <b>{bot_username}</b> en Telegram y envía " + mono("/start") + ". El bot sólo "
             "responde mientras el programa esté corriendo; para detenerlo presiona <b>Ctrl+C</b>."),
           P("Problemas comunes", "h2"),
           table([
               ["Mensaje / síntoma", "Solución"],
               ["Falta TELEGRAM_BOT_TOKEN", "El archivo .env no existe, está vacío o no se guardó."],
               ["InvalidToken / Unauthorized", "El token está mal copiado o fue revocado. Pide uno nuevo "
                "con /token en @BotFather."],
               ["Conflict: terminated by other getUpdates", "Hay otra copia del bot corriendo (otra "
                "terminal u otra computadora). Deja sólo una."],
               ["TimedOut / NetworkError", "Sin conexión a api.telegram.org (red, VPN o firewall)."],
               ["ModuleNotFoundError", "El entorno virtual no está activo o faltó "
                "pip install -r requirements.txt."],
           ], [5.6 * cm, 11.4 * cm])]
    return st


# ----------------------------------------------------------------------------- #
# Parte II — Uso del bot
# ----------------------------------------------------------------------------- #
def part_usage(bot_username):
    st = [P("6. Primeros pasos en Telegram", "h1"),
          numbered([
              "Abre Telegram y toca la lupa de búsqueda.",
              f"Escribe <b>{bot_username}</b> y abre el chat.",
              "Toca <b>Iniciar</b> (o envía " + mono("/start") + ").",
              "Bob te saluda con el botón <b>Explorar mercados</b> y ejemplos: toca uno para ver tu primer análisis.",
          ]),
          P("Consejo: el botón <b>Menú</b> junto al cuadro de texto muestra todos los comandos.", "callout")]

    st += [P("7. Explorar por mercado y sector", "h1"),
           P("Envía " + mono("/mercados") + " (o toca <b>Explorar mercados</b>) y navega con los botones: "
             "<b>mercado → sector → activo</b>. Al tocar un activo llega su análisis en velas diarias; "
             "debajo puedes cambiar a 1 hora o 4 horas."),
           P("Las emisoras del <b>SIC</b> (Sistema Internacional de Cotizaciones) se analizan con su "
             "ticker de origen en EE.UU., que tiene más historia e intradía; las señales técnicas son "
             "equivalentes a las de su réplica en la BMV.", "small"),
           Spacer(1, 4)]
    from catalog import MARKETS
    for m in MARKETS.values():
        rows = [["Sector", "Activos"]] + [
            [sector, ", ".join(f"{name} ({t.removesuffix('.MX')})" for t, name in items)]
            for sector, items in m["sectors"]]
        st += [KeepTogether([P(m["name"], "h2"), table(rows, [4.4 * cm, 12.6 * cm])])]

    st += [P("8. ¿Qué le puedo preguntar a Bob?", "h1"),
           P("Puedes escribirle como a un amigo o usar comandos. Así reconoce el activo:"),
           table([
               ["Escribes…", "Entiende", "Por qué"],
               ["¿Cómo ves a GOOG?", "GOOG", "Palabra en MAYÚSCULAS"],
               ["¿Qué opinas de Tesla?", "TSLA", "Nombre de empresa conocido"],
               ["$AMZN", "AMZN", "Símbolo con $"],
               ["aapl", "AAPL", "Mensaje de una sola palabra"],
               ["¿Compro bimbo?", "BIMBOA.MX", "Empresa mexicana conocida"],
               ["/analizar AAPL MSFT KO", "AAPL, MSFT, KO", "Comando (hasta 3 a la vez)"],
               ["Tesla en 4 horas", "TSLA · 4 horas", "Ventana de tiempo en el texto"],
               ["/analizar AAPL 1h", "AAPL · 1 hora", "Ventana de tiempo en el comando"],
           ], [5.6 * cm, 3.6 * cm, 7.8 * cm]),
           Spacer(1, 8),
           KeepTogether([P("Ventanas de tiempo", "h2"),
                         table([
                             ["Ventana", "Cada vela representa", "Historia usada", "Útil para"],
                             ["1 hora", "1 hora de operación", "60 días", "Movimientos de corto plazo"],
                             ["4 horas", "4 horas (se arma con velas de 1 h)", "200 días", "Swing de días a semanas"],
                             ["1 día (por defecto)", "1 sesión completa", "1 año", "Tendencia de mediano plazo"],
                         ], [3.4 * cm, 5.2 * cm, 3 * cm, 5.4 * cm]),
                         P("Se elige escribiéndola (" + mono("4h") + ", " + mono("1 hora") + ", " + mono("diario") +
                           ") o con los botones debajo de cada análisis.", "small")]),
           Spacer(1, 8),
           KeepTogether([P("Comandos", "h2"),
                         table([
                             ["Comando", "Qué hace"],
                             ["/mercados", "Explorar por mercado (BMV, SIC, ETFs) y sector"],
                             ["/analizar TICKER [ventana]", "Análisis del activo. Ej.: /analizar KO 4h"],
                             ["/ayuda", "Lista de comandos y ejemplos"],
                             ["/start", "Mensaje de bienvenida con botones de ejemplo"],
                         ], [5.6 * cm, 11.4 * cm])]),
           P("Símbolos útiles", "h2"),
           bullets([
               "<b>Acciones mexicanas:</b> agrega " + mono(".MX") + " — WALMEX.MX, CEMEXCPO.MX, "
               "GFNORTEO.MX, FEMSAUBD.MX.",
               "<b>Índices:</b> ^GSPC (S&amp;P 500), ^IXIC (Nasdaq), ^MXX (IPC de la BMV).",
               "<b>Cripto y divisas:</b> BTC-USD, ETH-USD, MXN=X (dólar/peso).",
           ])]

    chart_png, sample_ticker, txt = sample_output()
    intro = [P("9. Entendiendo la respuesta", "h1"),
             P("Llega <b>un solo mensaje</b>: el gráfico de velas con el análisis como texto debajo y "
               "botones para cambiar la ventana (1 hora · 4 horas · 1 día), <b>Actualizar</b> y volver a "
               "<b>Mercados</b>. La ventana activa aparece marcada con un punto.")]
    if not chart_png:
        st += intro
    else:
        img = Image(io.BytesIO(chart_png))
        ratio = img.imageHeight / img.imageWidth
        img.drawWidth, img.drawHeight = 15.5 * cm, 15.5 * cm * ratio
        st += [KeepTogether(intro + [img]),
               P(f"Figura 1. Gráfico real de {sample_ticker} generado por el bot.", "caption"),
               Table([[Paragraph(telegram_text_to_rl(txt), S["cell"])]], colWidths=[15.5 * cm],
                     style=[("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                            ("BOX", (0, 0), (-1, -1), 0.6, BLUE),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]),
               P("Figura 2. Texto del análisis que acompaña al gráfico.", "caption")]

    st += [P("El texto", "h2"),
           bullets([
               "<b>Encabezado:</b> ticker, nombre, último precio con su moneda y ventana de tiempo.",
               "<b>Señal:</b> COMPRA, VENTA o MANTENER, con su <b>fuerza</b> (ver tabla abajo).",
               "<b>Justificación:</b> por qué se llegó a esa señal.",
               "<b>Parabolic SAR:</b> la <b>tendencia</b>. Puntos debajo del precio = alcista; "
               "encima = bajista.",
               "<b>Estocástico:</b> el <b>impulso</b>. Arriba de 80 = sobrecompra (posiblemente caro); "
               "debajo de 20 = sobreventa (posiblemente barato).",
               "<b>Última vela:</b> fecha (y hora, en intradía) de la última vela usada.",
           ]),
           P("El gráfico", "h2"),
           bullets([
               "<b>Arriba:</b> velas japonesas — <font color='#16a34a'><b>verde</b></font> si cerró arriba de "
               "su apertura, <font color='#dc2626'><b>roja</b></font> si cerró abajo; el cuerpo va de apertura "
               "a cierre y la mecha marca máximo y mínimo. Los puntos son el SAR (verdes en tendencia alcista, "
               "rojos en bajista). La etiqueta azul marca el último precio y arriba a la derecha se indica la ventana.",
               "<b>Abajo:</b> líneas %K (azul) y %D (naranja). La franja roja es sobrecompra (&gt;80) y "
               "la verde, sobreventa (&lt;20).",
           ]),
           KeepTogether([
               P("¿Qué tan confiable es la señal?", "h2"),
               table([
                   ["Fuerza", "Significa"],
                   ["<font color='#16a34a'><b>Fuerte</b></font>", "Ambos indicadores coinciden."],
                   ["<font color='#2563eb'><b>Moderada</b></font>",
                    "Un indicador da la señal y el otro no la contradice."],
                   ["<font color='#d97706'><b>Débil</b></font>",
                    "El Estocástico da la señal, pero va contra la tendencia del SAR."],
                   ["<b>Mantener</b>", "No hay cruces nuevos o los indicadores se contradicen."],
               ], [3.4 * cm, 13.6 * cm])])]

    st += [P("10. Preguntas frecuentes", "h1"),
           P("<b>«No identifiqué ningún activo».</b> Escribe el ticker en MAYÚSCULAS, con $ "
             "(" + mono("$AAPL") + ") o usa " + mono("/analizar AAPL") + "."),
           P("<b>«No encontré datos para…».</b> Revisa el símbolo en finance.yahoo.com. Las acciones "
             "mexicanas llevan " + mono(".MX") + "."),
           P("<b>¿Cada cuándo se actualizan los datos?</b> Depende de la ventana (1 h, 4 h o 1 día); "
             "los datos se refrescan como máximo cada 5 minutos por activo y ventana."),
           P("<b>¿Por qué la señal cambia entre ventanas?</b> Cada ventana mide un horizonte distinto: "
             "puede haber tendencia alcista en diario y una corrección en 1 hora. Compararlas da contexto."),
           P("<b>El bot no contesta.</b> El programa " + mono("python main.py") + " tiene que estar "
             "corriendo en alguna computadora (ver sección 5).")]
    return st


# ----------------------------------------------------------------------------- #
# Parte III — Funcionamiento interno
# ----------------------------------------------------------------------------- #
def part_internals():
    st = [P("11. Arquitectura", "h1"),
          P(mono("bot_logic.py") + " es el único módulo que conoce Telegram; los demás son funciones "
            "que pueden probarse por separado."),
          architecture_diagram(), Spacer(1, 4),
          P("Figura 3. Módulos del proyecto y sus dependencias.", "caption")]

    st += [P("12. Componentes", "h1"),
           table([
               ["Archivo", "Responsabilidad", "Funciones clave"],
               ["main.py", "Punto de entrada.", "run_bot()"],
               ["config.py", "Lee el token y parámetros desde variables de entorno o " + mono(".env") +
                ". No contiene secretos.", "TELEGRAM_BOT_TOKEN, CHART_BARS"],
               ["bot_logic.py", "Handlers de Telegram, formato del mensaje (HTML), envío de la "
                "respuesta, botones y manejo global de errores.",
                "start_command, ayuda_command, analizar_command, handle_message, button_callback, "
                "mercados_command, perform_analysis, format_analysis"],
               ["ticker_parser.py", "Detecta el ticker en texto libre: <i>$TICKER</i>, nombres de "
                "empresas (Tesla, Bimbo…), palabras en MAYÚSCULAS o un mensaje de una sola palabra.",
                "extract_ticker, normalize_ticker"],
               ["catalog.py", "Catálogo para el menú: mercado (BMV, SIC, ETFs) → sector → activos.",
                "MARKETS, sectors, company_name"],
               ["data_provider.py", "Descarga velas OHLCV y precio actual con <b>un solo</b> objeto "
                "yfinance según la ventana (1h, 4h, 1d). Las de 4 h se arman agrupando velas de 1 h. "
                "Caché de 5 minutos.", "get_market_data, resample_hours, TIMEFRAMES"],
               ["technical_analysis.py", "Calcula PSAR y Estocástico con pandas/numpy e interpreta "
                "las señales.", "compute_indicators, analyze → Analysis"],
               ["charts.py", "Gráfico de velas + SAR y Estocástico, sin huecos de noches ni fines de "
                "semana. API orientada a objetos, segura en hilos.", "build_chart → bytes PNG"],
               ["query_logger.py", "Agrega cada consulta a <i>consultas_bot.csv</i> con un candado "
                "para escrituras concurrentes.", "log_query"],
           ], [4.0 * cm, 7.6 * cm, 5.4 * cm])]

    st += [P("13. Flujo de una consulta", "h1"),
           P("Ejemplo: el usuario escribe <i>«¿Qué opinas de Tesla?»</i>."),
           flow_diagram(), Spacer(1, 4),
           P("Figura 4. Flujo de ejecución. El paso 4 corre en un hilo para no bloquear al bot.", "caption"),
           P("Detalle de cada paso", "h2"),
           numbered([
               "<b>Recepción.</b> " + mono("run_polling()") + " recibe el mensaje. Si es texto libre lo "
               "atiende " + mono("handle_message") + "; si es comando, " + mono("analizar_command") +
               " (hasta 3 tickers y ventana opcional); " + mono("/mercados") + " abre el menú; si es un botón, "
               + mono("button_callback") + " navega el menú o lanza el análisis.",
               "<b>Ticker.</b> " + mono("extract_ticker") + " devuelve <i>TSLA</i> porque «tesla» está "
               "en la tabla de alias. Si no encuentra nada, el bot explica cómo escribirlo.",
               "<b>Indicador de actividad.</b> El chat muestra «enviando foto…» mientras se trabaja.",
               "<b>Trabajo pesado en un hilo.</b> Descarga, cálculo y gráfico ocurren dentro de "
               + mono("asyncio.to_thread") + ", así otros usuarios no esperan.",
               "<b>Respuesta única.</b> El análisis va como pie de foto (si cabe en 1024 caracteres) con "
               "el botón <i>Actualizar</i>; si no cabe, se envía la foto y luego el texto.",
               "<b>Registro.</b> Se guarda la consulta en el CSV (también en un hilo).",
           ])]

    st += [KeepTogether([
           P("14. Indicadores técnicos", "h1"),
           P("14.1 Parabolic SAR (0.02 / 0.2)", "h2"),
           P("Sigue la tendencia con un punto que se acerca al precio cada día. Con EP = precio extremo "
             "de la tendencia actual y AF = factor de aceleración:"),
           code("SAR(t) = SAR(t-1) + AF * (EP - SAR(t-1))\n"
                "AF inicia en 0.02 y sube 0.02 en cada nuevo extremo, hasta 0.20\n"
                "Si el precio cruza el SAR, la tendencia se invierte: SAR = EP anterior")]),
           P("Además del valor, se guarda la <b>tendencia</b> (+1 alcista, −1 bajista). Un cambio de "
             "tendencia entre ayer y hoy es la señal de Compra o Venta."),
           P("14.2 Oscilador Estocástico lento (14, 3, 3)", "h2"),
           code("%K bruto = 100 * (Cierre - Mínimo14) / (Máximo14 - Mínimo14)\n"
                "%K = media móvil 3 de %K bruto\n"
                "%D = media móvil 3 de %K"),
           P("Compra: %K cruza por encima de %D estando en sobreventa (&lt;20). "
             "Venta: %K cruza por debajo de %D en sobrecompra (&gt;80).")]

    st += [KeepTogether([
        P("15. Señal combinada", "h1"),
        table([
            ["Parabolic SAR", "Estocástico", "Señal final", "Fuerza"],
            ["Compra", "Compra", "<font color='#16a34a'><b>Compra</b></font>", "Fuerte"],
            ["Venta", "Venta", "<font color='#dc2626'><b>Venta</b></font>", "Fuerte"],
            ["Compra / Venta", "Mantener", "La del SAR", "Moderada"],
            ["Mantener (tendencia a favor)", "Compra / Venta", "La del Estocástico", "Moderada"],
            ["Mantener (tendencia en contra)", "Compra / Venta", "La del Estocástico", "Débil"],
            ["Compra", "Venta (o al revés)", "<font color='#d97706'><b>Mantener</b></font>", "—"],
            ["Mantener", "Mantener", "<font color='#d97706'><b>Mantener</b></font>", "—"],
        ], [4.6 * cm, 3.6 * cm, 4.4 * cm, 4.4 * cm])])]

    st += [P("16. Decisiones de diseño y rendimiento", "h1"),
           bullets([
               "<b>No bloquear al bot:</b> yfinance y matplotlib son síncronos, por eso corren en hilos "
               "y varias consultas se atienden en paralelo (" + mono("concurrent_updates(True)") + ").",
               "<b>Una sola descarga por consulta:</b> histórico y precio salen del mismo "
               + mono("yf.Ticker") + ".",
               "<b>Caché de 5 minutos</b> por ticker: el botón <i>Actualizar</i> o consultas repetidas "
               "responden al instante.",
               "<b>Indicadores calculados una vez</b> y reutilizados para la señal y el gráfico.",
               "<b>Velas de 4 horas:</b> Yahoo no las ofrece; se agrupan velas de 1 h por sesión en bloques "
               "de 4, sin cruzar cierres de mercado (en cripto, 24/7, salen 6 velas por día).",
               "<b>Menú con edición en sitio:</b> navegar mercados y sectores edita el mismo mensaje en "
               "lugar de llenar el chat; los datos de cada botón (" + mono("m:MX") + ", " + mono("s:MX:0") +
               ", " + mono("a:TICKER:4h") + ") caben en el límite de 64 bytes de Telegram.",
               "<b>Sin pandas_ta:</b> las fórmulas están en pandas puro (~40 líneas), sin depender de "
               "una librería sin mantenimiento.",
               "<b>HTML en lugar de Markdown</b> para los mensajes: el texto se escapa y no se rompe con "
               "caracteres especiales.",
           ]),
           P("Variable opcional en " + mono(".env") + ": " + mono("BOB_CHART_BARS") +
             " (velas en el gráfico, por defecto 120). La historia de cada ventana se ajusta en "
             + mono("TIMEFRAMES") + " de " + mono("data_provider.py") + ".")]

    st += [P("17. Cómo extender el bot", "h1"),
           bullets([
               "<b>Nuevo indicador:</b> agregar su cálculo en " + mono("compute_indicators") + ", una "
               "función " + mono("analyze_xxx") + " que devuelva " + mono("IndicatorResult") +
               " y sumarlo en " + mono("analyze()") + ".",
               "<b>Nuevo alias de empresa:</b> añadir la entrada en " + mono("COMPANY_ALIASES") + ".",
               "<b>Nuevo activo o sector en el menú:</b> agregar " + mono("(ticker, nombre)") + " en "
               + mono("catalog.py") + "; el manual lo incluye al regenerarlo.",
               "<b>Nuevo comando:</b> crear el handler en " + mono("bot_logic.py") + ", registrarlo en "
               + mono("run_bot()") + " y en " + mono("_post_init") + " para que aparezca en el menú.",
               "<b>Regenerar este manual:</b> " + mono("python docs/generar_pdfs.py") + ".",
           ])]
    return st


def disclaimer():
    return [KeepTogether([
        P("Descargo de responsabilidad", "h1"),
        P("Bob es un bot automático y sus análisis se basan exclusivamente en dos indicadores técnicos. "
          "Su propósito es <b>educativo</b>.<br/><br/>"
          "<b>Sus recomendaciones NO constituyen asesoría financiera.</b> Haz tu propia investigación y, "
          "si es necesario, consulta a un profesional antes de comprar o vender. Invertir conlleva "
          "riesgos, incluida la pérdida del capital.", "callout"),
        Spacer(1, 6), P(f"Actualizado: {date.today():%d/%m/%Y}", "small")])]


def manual(out, bot_username):
    st = cover("Bob the Bot", "Manual completo: creación, uso y funcionamiento del bot de "
                              "análisis bursátil para Telegram")
    st += [P("Contenido", "h2"),
           table([
               ["Parte", "Secciones", "Para quién"],
               ["I. Puesta en marcha", "1–5 · Requisitos, @BotFather, instalación, token, ejecución",
                "Quien instala el bot"],
               ["II. Uso del bot", "6–10 · Primeros pasos, mercados y sectores, consultas y ventanas, respuesta, FAQ",
                "Usuarios en Telegram"],
               ["III. Funcionamiento interno", "11–17 · Arquitectura, flujo, indicadores, señal, "
                "diseño, extensiones", "Desarrolladores"],
           ], [4.4 * cm, 8.6 * cm, 4 * cm]),
           Spacer(1, 10),
           P(f"Bob the Bot (<b>{bot_username}</b>) recibe consultas sobre activos financieros en "
             "Telegram, descarga datos de Yahoo! Finance, calcula el <b>Parabolic SAR</b> y el "
             "<b>Oscilador Estocástico</b> y responde con una señal (Compra / Venta / Mantener), su "
             "justificación y un gráfico.")]

    st += part_header("I", "Puesta en marcha", "De @BotFather a tener el bot respondiendo en Telegram")
    st += part_setup(bot_username)
    st += part_header("II", "Uso del bot", "Cómo hacer consultas e interpretar las respuestas")
    st += part_usage(bot_username)
    st += part_header("III", "Funcionamiento interno", "Arquitectura, flujo del código e indicadores")
    st += part_internals()
    st += disclaimer()
    build(out, st, "Manual")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bot-username", default="@BobAnalisisBursatil_bot",
                    help="usuario de Telegram del bot")
    ap.add_argument("--out", default=str(ROOT), help="carpeta de salida")
    args = ap.parse_args()
    manual(Path(args.out) / "Manual_Bob_the_Bot.pdf", args.bot_username)
