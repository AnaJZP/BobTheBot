"""Capa de Telegram: comandos, mensajes y envío de respuestas.

Este módulo solo coordina. Los datos, los indicadores, las reglas de señal y las
gráficas viven en sus propios módulos.
"""
import asyncio
import html
import logging

from telegram import BotCommand, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler,
                          filters)

import config
from charts import grafica_analisis
from data_provider import get_quote, get_stock_data
from query_logger import log_query
from technical_analysis import analizar
from ticker_parser import extract_ticker

log = logging.getLogger(__name__)

COMANDOS = [
    BotCommand("start", "Iniciar conversación"),
    BotCommand("analizar", "Analizar un activo, p. ej. /analizar AAPL"),
    BotCommand("ayuda", "Ver ejemplos de uso"),
]
EMOJI = {"Compra": "🟢", "Venta": "🔴", "Mantener": "🟡"}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    nombre = html.escape(update.effective_user.first_name or "")
    await update.effective_message.reply_text(
        f"¡Hola {nombre}! 👋 Soy Bob, tu asistente de análisis bursátil.\n"
        "Pregúntame, por ejemplo: «¿Compro o vendo AMZN?», «¿Cómo ves a Walmex?» "
        "o usa /analizar TSLA.\nEscribe /ayuda para ver más ejemplos."
    )


async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "🤖 Comandos:\n"
        "/analizar TICKER – análisis de un activo (ej. /analizar AAPL, /analizar WALMEX.MX)\n"
        "/ayuda – esta ayuda\n\n"
        "También entiendo mensajes como:\n"
        "  • ¿Compro o vendo MSFT?\n  • Análisis de $NVDA\n  • ¿Qué opinas de Tesla?\n"
        "  • ¿Cómo va el IPC?\n\n"
        "Emisoras de la BMV: usa el sufijo .MX (GFNORTEO.MX, AMXB.MX).\n"
        "Señales basadas en Parabolic SAR y Oscilador Estocástico (14,3,3)."
    )


async def analizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Indica un ticker. Ejemplo: /analizar AAPL")
        return
    ticker = context.args[0].upper()
    await perform_analysis(update, ticker, f"/analizar {ticker}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = update.effective_message.text or ""
    ticker = extract_ticker(texto)
    if not ticker:
        await update.effective_message.reply_text(
            "No identifiqué un activo en tu mensaje. Prueba con «Análisis de AAPL», "
            "«$TSLA» o /analizar WALMEX.MX")
        return
    await perform_analysis(update, ticker, texto)


def _formatear(a, precio: float, moneda: str) -> str:
    e = html.escape
    return (
        f"🔔 <b>Análisis para {e(a.ticker)}</b>\n\n"
        f"<b>Precio actual:</b> {precio:,.2f} {e(moneda)}\n"
        f"<b>Señal sugerida:</b> {EMOJI.get(a.senal, '')} <b>{e(a.senal.upper())}</b>\n"
        f"{e(a.justificacion)}\n\n"
        f"📊 <b>Parabolic SAR:</b> {e(a.sar.senal)}\n<i>{e(a.sar.nota)}</i>\n\n"
        f"📉 <b>Estocástico (14,3,3):</b> {e(a.estocastico.senal)}\n"
        f"<i>{e(a.estocastico.nota)}</i>\n\n"
        "🎓 <i>Recomendación automatizada con fines educativos; no constituye "
        "asesoramiento financiero.</i>"
    )


async def perform_analysis(update: Update, ticker: str, query_text: str) -> None:
    msg, user = update.effective_message, update.effective_user
    await msg.reply_text(f"🔍 Analizando {ticker}…")
    await msg.chat.send_action(ChatAction.TYPING)

    # Las llamadas de red y de cálculo son bloqueantes: se ejecutan en un hilo
    # aparte para que el bot siga atendiendo a otros usuarios mientras tanto.
    df = await asyncio.to_thread(get_stock_data, ticker, config.PERIODO_DATOS,
                                 config.INTERVALO_DATOS)
    if df is None or len(df) < 30:
        await msg.reply_text(f"No pude obtener suficientes datos de {ticker}. "
                             "Verifica el símbolo (emisoras mexicanas: sufijo .MX).")
        log_query(user.id, user.first_name, ticker, query_text, "Error", "Sin datos")
        return

    precio, moneda = await asyncio.to_thread(get_quote, ticker, df)
    a = await asyncio.to_thread(analizar, df, ticker)
    await msg.reply_text(_formatear(a, precio, moneda), parse_mode=ParseMode.HTML)
    log_query(user.id, user.first_name, ticker, query_text, a.senal, a.justificacion)

    if config.ENVIAR_GRAFICA:
        await msg.chat.send_action(ChatAction.UPLOAD_PHOTO)
        imagen = await asyncio.to_thread(grafica_analisis, a.datos, ticker, config.DIAS_GRAFICA)
        await msg.reply_photo(photo=imagen, caption=f"{ticker}: precio, SAR y Estocástico")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Error no controlado", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Ocurrió un error inesperado. Intenta de nuevo en un momento.")


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands(COMANDOS)   # menú de comandos en Telegram


def build_app(token: str) -> Application:
    app = Application.builder().token(token).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["ayuda", "help"], ayuda_command))
    app.add_handler(CommandHandler("analizar", analizar_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app


def run_bot() -> None:
    logging.basicConfig(format="%(asctime)s  %(levelname)s  %(name)s: %(message)s",
                        level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)   # oculta el token de las URLs
    app = build_app(config.get_token())
    log.info("Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
