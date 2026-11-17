"""Lógica de Telegram: comandos, mensajes libres y envío del análisis."""
from __future__ import annotations

import asyncio
import html
import logging

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update, User)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from charts import build_chart
from config import CHART_DAYS, HISTORY_PERIOD, TELEGRAM_BOT_TOKEN
from data_provider import get_market_data
from query_logger import log_query
from technical_analysis import COMPRA, VENTA, Analysis, analyze
from ticker_parser import extract_ticker, normalize_ticker

log = logging.getLogger(__name__)

MAX_TICKERS_PER_COMMAND = 3
CAPTION_LIMIT = 1024  # límite de Telegram para el texto de una foto
SIGNAL_EMOJI = {COMPRA: "🟢", VENTA: "🔴"}

HELP_TEXT = (
    "🤖 <b>¿Qué puedo hacer?</b>\n\n"
    "/analizar <code>TICKER</code> – análisis de un activo (ej. <code>/analizar AAPL</code>)\n"
    "   Puedes pedir hasta 3: <code>/analizar AAPL MSFT KO</code>\n"
    "/ayuda – esta ayuda\n\n"
    "También entiendo mensajes como:\n"
    "• ¿Compro o vendo MSFT?\n"
    "• ¿Qué opinas de Tesla?\n"
    "• $AMZN\n"
    "• bimbo  ·  WALMEX.MX  ·  BTC-USD\n\n"
    "Uso <b>Parabolic SAR</b> (tendencia) y <b>Oscilador Estocástico 14-3-3</b> (impulso).\n"
    "<i>Herramienta educativa: no es asesoría financiera.</i>"
)


# --------------------------------------------------------------------------- #
# Comandos básicos
# --------------------------------------------------------------------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = html.escape(update.effective_user.first_name or "")
    await update.message.reply_html(
        f"¡Hola {name}! 👋 Soy <b>Bob</b>, tu asistente de análisis bursátil.\n\n"
        "Escríbeme algo como <i>«¿Qué opinas de TSLA?»</i> o usa <code>/analizar AAPL</code>.\n"
        "Toca un botón para probar:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t, callback_data=f"analizar:{t}") for t in ("AAPL", "TSLA", "WALMEX.MX")
        ]]),
    )


async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(HELP_TEXT)


# --------------------------------------------------------------------------- #
# Entradas de análisis
# --------------------------------------------------------------------------- #
async def analizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_html("Indica un ticker. Ejemplo: <code>/analizar AAPL</code>")
        return

    tickers = list(dict.fromkeys(filter(None, map(normalize_ticker, context.args))))
    if not tickers:
        await update.message.reply_text("Ese símbolo no parece válido. Ejemplo: /analizar AAPL")
        return
    if len(tickers) > MAX_TICKERS_PER_COMMAND:
        await update.message.reply_text(f"Analizaré solo los primeros {MAX_TICKERS_PER_COMMAND}.")
        tickers = tickers[:MAX_TICKERS_PER_COMMAND]

    for t in tickers:
        await perform_analysis(update.message, update.effective_user, t, update.message.text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    ticker = extract_ticker(text)
    if not ticker:
        await update.message.reply_html(
            "No identifiqué ningún activo 🤔\n"
            "Escribe el ticker en mayúsculas (ej. <i>«¿Cómo ves GOOG?»</i>), con $ (<code>$AMZN</code>) "
            "o usa <code>/analizar TICKER</code>."
        )
        return
    await perform_analysis(update.message, update.effective_user, ticker, text)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, ticker = (query.data or "").partition(":")
    if ticker := normalize_ticker(ticker):
        await perform_analysis(query.message, query.from_user, ticker, f"[botón] {ticker}")


# --------------------------------------------------------------------------- #
# Análisis
# --------------------------------------------------------------------------- #
def _run_pipeline(ticker: str) -> tuple[Analysis, float, str | None, bytes | None] | None:
    """Trabajo bloqueante (red + cálculo + gráfico). Se ejecuta en un hilo aparte."""
    md = get_market_data(ticker, period=HISTORY_PERIOD)
    if md is None or len(md.history) < 30:
        return None
    analysis = analyze(md.history, ticker)
    try:
        chart = build_chart(analysis, days=CHART_DAYS)
    except Exception:
        log.exception("Error generando gráfico de %s", ticker)
        chart = None
    return analysis, md.price, md.currency, chart


def format_analysis(a: Analysis, price: float, currency: str | None) -> str:
    e = html.escape
    emoji = SIGNAL_EMOJI.get(a.signal, "🟡")
    strength = f" <i>({a.strength.lower()})</i>" if a.strength else ""
    cur = f" {e(currency)}" if currency else ""
    return (
        f"<b>📊 {e(a.ticker)}</b>  ·  {price:,.2f}{cur}\n"
        f"{emoji} Señal: <b>{a.signal.upper()}</b>{strength}\n"
        f"{e(a.justification)}\n\n"
        f"<b>Parabolic SAR</b> — {e(a.psar.summary)}\n"
        f"{e(a.psar.note)}\n\n"
        f"<b>Estocástico 14-3-3</b> — {e(a.stoch.summary)}\n"
        f"{e(a.stoch.note)}\n\n"
        f"<i>Datos al {a.last_date:%d/%m/%Y}. Educativo, no es asesoría financiera.</i>"
    )


async def perform_analysis(message: Message, user: User, ticker: str, query_text: str) -> None:
    await message.chat.send_action(ChatAction.UPLOAD_PHOTO)

    result = await asyncio.to_thread(_run_pipeline, ticker)
    if result is None:
        await message.reply_html(
            f"No encontré datos para <b>{html.escape(ticker)}</b>. Revisa el símbolo "
            "(las acciones mexicanas llevan <code>.MX</code>, ej. <code>WALMEX.MX</code>)."
        )
        await asyncio.to_thread(log_query, user.id, user.first_name, ticker, query_text,
                                "Error", "Sin datos")
        return

    analysis, price, currency, chart = result
    text = format_analysis(analysis, price, currency)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Actualizar", callback_data=f"analizar:{ticker}")]])

    if chart and len(text) <= CAPTION_LIMIT:
        await message.reply_photo(chart, caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        if chart:
            await message.reply_photo(chart)
        await message.reply_html(text, reply_markup=keyboard)

    await asyncio.to_thread(log_query, user.id, user.first_name, ticker, query_text,
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
        BotCommand("analizar", "Analizar un activo (ej. /analizar AAPL)"),
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
    app.add_handler(CommandHandler("analizar", analizar_command))
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r"^analizar:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    log.info("Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
