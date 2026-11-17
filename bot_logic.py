"""Lógica de Telegram: comandos, menú de mercados, mensajes libres y envío del análisis."""
from __future__ import annotations

import asyncio
import html
import logging

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update, User)
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from catalog import MARKETS, company_name, market_name, sectors
from charts import build_chart
from config import CHART_BARS, TELEGRAM_BOT_TOKEN
from data_provider import DEFAULT_TIMEFRAME, TIMEFRAME_LABELS, TIMEFRAMES, get_market_data
from query_logger import log_query
from technical_analysis import COMPRA, VENTA, Analysis, analyze
from ticker_parser import STOPWORDS, extract_ticker, extract_timeframe, normalize_ticker

log = logging.getLogger(__name__)

MAX_TICKERS_PER_COMMAND = 3
CAPTION_LIMIT = 1024  # límite de Telegram para el texto de una foto
SIGNAL_EMOJI = {COMPRA: "🟢", VENTA: "🔴"}

HELP_TEXT = (
    "🤖 <b>¿Qué puedo hacer?</b>\n\n"
    "/mercados – explorar por mercado y sector (BMV, SIC, ETFs)\n"
    "/analizar <code>TICKER</code> – análisis de un activo (ej. <code>/analizar AAPL</code>)\n"
    "   Con ventana de tiempo: <code>/analizar AAPL 4h</code>  (1h · 4h · 1d)\n"
    "   Hasta 3 a la vez: <code>/analizar AAPL MSFT KO</code>\n"
    "/ayuda – esta ayuda\n\n"
    "También entiendo mensajes como:\n"
    "• ¿Compro o vendo MSFT?\n"
    "• ¿Qué opinas de Tesla en 1 hora?\n"
    "• $AMZN 4h\n"
    "• bimbo  ·  WALMEX.MX  ·  BTC-USD\n\n"
    "Uso <b>Parabolic SAR</b> (tendencia) y <b>Oscilador Estocástico 14-3-3</b> (impulso) "
    "sobre un gráfico de velas.\n"
    "<i>Herramienta educativa: no es asesoría financiera.</i>"
)


# --------------------------------------------------------------------------- #
# Teclados
# --------------------------------------------------------------------------- #
def _short(ticker: str) -> str:
    return ticker.removesuffix(".MX")


def markets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(m["name"], callback_data=f"m:{code}")]
                                 for code, m in MARKETS.items()])


def sectors_keyboard(code: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{name} ({len(items)})", callback_data=f"s:{code}:{i}")]
            for i, (name, items) in enumerate(sectors(code))]
    rows.append([InlineKeyboardButton("« Mercados", callback_data="m")])
    return InlineKeyboardMarkup(rows)


def tickers_keyboard(code: str, idx: int) -> InlineKeyboardMarkup:
    _, items = sectors(code)[idx]
    buttons = [InlineKeyboardButton(f"{name} · {_short(t)}", callback_data=f"a:{t}:{DEFAULT_TIMEFRAME}")
               for t, name in items]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("« Sectores", callback_data=f"m:{code}"),
                 InlineKeyboardButton("« Mercados", callback_data="m")])
    return InlineKeyboardMarkup(rows)


def analysis_keyboard(ticker: str, timeframe: str) -> InlineKeyboardMarkup:
    tf_row = [InlineKeyboardButton(("• " if tf == timeframe else "") + TIMEFRAME_LABELS[tf],
                                   callback_data=f"a:{ticker}:{tf}") for tf in TIMEFRAMES]
    return InlineKeyboardMarkup([
        tf_row,
        [InlineKeyboardButton("🔄 Actualizar", callback_data=f"a:{ticker}:{timeframe}"),
         InlineKeyboardButton("📂 Mercados", callback_data="m")],
    ])


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = html.escape(update.effective_user.first_name or "")
    await update.message.reply_html(
        f"¡Hola {name}! 👋 Soy <b>Bob</b>, tu asistente de análisis bursátil.\n\n"
        "Escríbeme algo como <i>«¿Qué opinas de TSLA?»</i>, usa <code>/analizar AAPL 4h</code> "
        "o explora por mercado y sector:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📂 Explorar mercados", callback_data="m")]]
            + [[InlineKeyboardButton(t, callback_data=f"a:{t}:{DEFAULT_TIMEFRAME}")
                for t in ("AAPL", "WALMEX.MX", "SPY")]]
        ),
    )


async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(HELP_TEXT)


async def mercados_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html("📂 <b>Elige un mercado</b>", reply_markup=markets_keyboard())


async def analizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_html(
            "Indica un ticker. Ejemplo: <code>/analizar AAPL</code> o <code>/analizar AAPL 4h</code>.\n"
            "También puedes usar /mercados para elegirlo de una lista.")
        return

    timeframe = extract_timeframe(" ".join(context.args)) or DEFAULT_TIMEFRAME
    candidates = [a for a in context.args
                  if not extract_timeframe(a) and a.upper() not in STOPWORDS]
    tickers = list(dict.fromkeys(filter(None, map(normalize_ticker, candidates))))
    if not tickers:
        await update.message.reply_text("Ese símbolo no parece válido. Ejemplo: /analizar AAPL")
        return
    if len(tickers) > MAX_TICKERS_PER_COMMAND:
        await update.message.reply_text(f"Analizaré solo los primeros {MAX_TICKERS_PER_COMMAND}.")
        tickers = tickers[:MAX_TICKERS_PER_COMMAND]

    for t in tickers:
        await perform_analysis(update.message, update.effective_user, t, timeframe, update.message.text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    ticker = extract_ticker(text)
    if not ticker:
        await update.message.reply_html(
            "No identifiqué ningún activo 🤔\n"
            "Escribe el ticker en mayúsculas (ej. <i>«¿Cómo ves GOOG?»</i>), con $ (<code>$AMZN</code>), "
            "usa <code>/analizar TICKER</code> o elígelo de la lista:",
            reply_markup=markets_keyboard(),
        )
        return
    timeframe = extract_timeframe(text) or DEFAULT_TIMEFRAME
    await perform_analysis(update.message, update.effective_user, ticker, timeframe, text)


# --------------------------------------------------------------------------- #
# Botones
# --------------------------------------------------------------------------- #
async def _show_menu(query, text: str, markup: InlineKeyboardMarkup) -> None:
    """Edita el menú en el mismo mensaje; si viene de una foto, envía uno nuevo."""
    if query.message.photo:
        await query.message.reply_html(text, reply_markup=markup)
        return
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    except BadRequest as e:  # "message is not modified" u otro mensaje no editable
        if "not modified" not in str(e).lower():
            await query.message.reply_html(text, reply_markup=markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    kind, _, rest = data.partition(":")

    if kind == "a" or kind == "analizar":  # "analizar:" = botones de versiones anteriores
        ticker_raw, _, tf = rest.partition(":")
        ticker = normalize_ticker(ticker_raw)
        tf = tf if tf in TIMEFRAMES else DEFAULT_TIMEFRAME
        if not ticker:
            await query.answer()
            return
        await query.answer(f"Analizando {ticker} · {TIMEFRAME_LABELS[tf]}…")
        await perform_analysis(query.message, query.from_user, ticker, tf, f"[botón] {ticker} {tf}")
        return

    await query.answer()
    if kind == "m" and not rest:
        await _show_menu(query, "📂 <b>Elige un mercado</b>", markets_keyboard())
    elif kind == "m" and rest in MARKETS:
        await _show_menu(query, f"📂 <b>{html.escape(market_name(rest))}</b>\nElige un sector:",
                         sectors_keyboard(rest))
    elif kind == "s":
        code, _, idx = rest.partition(":")
        if code in MARKETS and idx.isdigit() and int(idx) < len(sectors(code)):
            name = sectors(code)[int(idx)][0]
            await _show_menu(query, f"📂 <b>{html.escape(market_name(code))} › {html.escape(name)}</b>\n"
                                    "Elige un activo:", tickers_keyboard(code, int(idx)))


# --------------------------------------------------------------------------- #
# Análisis
# --------------------------------------------------------------------------- #
def _run_pipeline(ticker: str, timeframe: str) -> tuple[Analysis, float, str | None, bytes | None] | None:
    """Trabajo bloqueante (red + cálculo + gráfico). Se ejecuta en un hilo aparte."""
    md = get_market_data(ticker, timeframe)
    if md is None or len(md.history) < 30:
        return None
    analysis = analyze(md.history, ticker, timeframe)
    try:
        chart = build_chart(analysis, bars=CHART_BARS)
    except Exception:
        log.exception("Error generando gráfico de %s", ticker)
        chart = None
    return analysis, md.price, md.currency, chart


def format_analysis(a: Analysis, price: float, currency: str | None) -> str:
    e = html.escape
    emoji = SIGNAL_EMOJI.get(a.signal, "🟡")
    strength = f" <i>({a.strength.lower()})</i>" if a.strength else ""
    cur = f" {e(currency)}" if currency else ""
    name = company_name(a.ticker)
    header = f"<b>📊 {e(a.ticker)}</b>" + (f" · {e(name)}" if name else "")
    date_fmt = "%d/%m/%Y" if a.timeframe == "1d" else "%d/%m/%Y %H:%M"
    return (
        f"{header}\n"
        f"💲 {price:,.2f}{cur}  ·  ⏱ {TIMEFRAME_LABELS.get(a.timeframe, a.timeframe)}\n"
        f"{emoji} Señal: <b>{a.signal.upper()}</b>{strength}\n"
        f"{e(a.justification)}\n\n"
        f"<b>Parabolic SAR</b> — {e(a.psar.summary)}\n"
        f"{e(a.psar.note)}\n\n"
        f"<b>Estocástico 14-3-3</b> — {e(a.stoch.summary)}\n"
        f"{e(a.stoch.note)}\n\n"
        f"<i>Última vela: {a.last_date:{date_fmt}}. Educativo, no es asesoría financiera.</i>"
    )


async def perform_analysis(message: Message, user: User, ticker: str, timeframe: str,
                           query_text: str) -> None:
    await message.chat.send_action(ChatAction.UPLOAD_PHOTO)

    result = await asyncio.to_thread(_run_pipeline, ticker, timeframe)
    if result is None:
        await message.reply_html(
            f"No encontré datos suficientes para <b>{html.escape(ticker)}</b> "
            f"({TIMEFRAME_LABELS.get(timeframe, timeframe)}). Revisa el símbolo "
            "(las acciones mexicanas llevan <code>.MX</code>, ej. <code>WALMEX.MX</code>) "
            "o prueba otra ventana de tiempo.",
            reply_markup=markets_keyboard(),
        )
        await asyncio.to_thread(log_query, user.id, user.first_name, ticker, query_text,
                                "Error", "Sin datos")
        return

    analysis, price, currency, chart = result
    text = format_analysis(analysis, price, currency)
    keyboard = analysis_keyboard(ticker, timeframe)

    if chart and len(text) <= CAPTION_LIMIT:
        await message.reply_photo(chart, caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        if chart:
            await message.reply_photo(chart)
        await message.reply_html(text, reply_markup=keyboard)

    await asyncio.to_thread(log_query, user.id, user.first_name, ticker, f"{query_text} [{timeframe}]",
                            analysis.signal, analysis.justification)


# --------------------------------------------------------------------------- #
# Arranque
# --------------------------------------------------------------------------- #
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Error procesando update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("Ups, algo salió mal. Intenta de nuevo en un momento.")
        except Exception:
            pass


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("mercados", "Explorar por mercado y sector"),
        BotCommand("analizar", "Analizar un activo (ej. /analizar AAPL 4h)"),
        BotCommand("ayuda", "Ver comandos y ejemplos"),
        BotCommand("start", "Mensaje de bienvenida"),
    ])


def run_bot() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN. Crea un archivo .env con la línea "
                         "TELEGRAM_BOT_TOKEN=<tu token> o exporta la variable de entorno.")

    app = (Application.builder().token(TELEGRAM_BOT_TOKEN)
           .concurrent_updates(True).post_init(_post_init).build())

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["ayuda", "help"], ayuda_command))
    app.add_handler(CommandHandler("mercados", mercados_command))
    app.add_handler(CommandHandler("analizar", analizar_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    log.info("Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
